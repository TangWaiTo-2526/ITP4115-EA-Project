import secrets
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from sqlalchemy import func, or_
from werkzeug.security import generate_password_hash

from flask import render_template, flash, redirect, url_for, request, g, session, abort
from flask_login import login_user, logout_user, current_user, login_required
from flask_babel import _, get_locale
from app import app, db
from app.forms import (
    LoginForm,
    RegistrationForm,
    EmailVerificationForm,
    RegisterExtraForm,
    ResendVerifyForm,
    EditProfileForm,
    DeliveryAddressForm,
    ResetPasswordRequestForm,
    ResetPasswordForm,
)
from app.models import (
    User,
    UserAddress,
    Membership,
    MembershipPointsLog,
    RegistrationVerificationCode,
    ProductCategory,
    ProductDetail,
)
from app.category_catalog import build_browse_page
from app.email import send_password_reset_email, send_registration_verification_email
from app.hk_address import HK_DISTRICTS


REG_VERIFY_TTL_SEC = 900
REG_VERIFY_IP_COOLDOWN_MIN = 15


def _populate_edit_profile_form(form, user):
    form.salutation.data = user.salutation or ''
    form.username.data = user.user_name
    form.nationality.data = user.nationality or ''
    form.mobile_phone.data = user.phone_number or ''
    form.mail.data = user.mail
    form.comm_language.data = user.communication_language or '繁體'
    form.birthday.data = user.birthday
    form.marketing_opt_out.data = bool(user.marketing_opt_out)
    form.brand_fortress.data = bool(user.brand_fortress)
    form.brand_parknshop.data = bool(user.brand_parknshop)
    form.brand_watsons.data = bool(user.brand_watsons)
    form.brand_moneyback.data = bool(user.brand_moneyback)

    addr = user.addresses.order_by(UserAddress.create_time.asc()).first()
    if addr:
        form.home_phone.data = addr.home_phone or ''
        form.addr_unit.data = addr.unit or ''
        form.addr_floor.data = addr.floor or ''
        form.addr_building_street.data = addr.building_street or ''
        r = (addr.region or '').strip()
        form.addr_region.data = r
        if r in HK_DISTRICTS:
            form.addr_district.choices = [('', '請選擇')] + [(d, d) for d in HK_DISTRICTS[r]]
        else:
            form.addr_district.choices = [('', '請選擇')]
        form.addr_district.data = addr.district or ''
    else:
        form.home_phone.data = ''
        form.addr_unit.data = ''
        form.addr_floor.data = ''
        form.addr_building_street.data = ''
        form.addr_region.data = ''
        form.addr_district.choices = [('', '請選擇')]
        form.addr_district.data = ''


def _save_profile_and_address(form, user):
    user.salutation = (form.salutation.data or '').strip() or None
    user.user_name = (form.username.data or '').strip()
    user.mail = (form.mail.data or '').strip()
    ph = (form.mobile_phone.data or '').strip()
    user.phone_number = ph if ph else None
    user.birthday = form.birthday.data
    user.nationality = (form.nationality.data or '').strip() or None
    user.communication_language = (form.comm_language.data or '繁體').strip()
    user.marketing_opt_out = bool(form.marketing_opt_out.data)
    user.brand_fortress = bool(form.brand_fortress.data)
    user.brand_parknshop = bool(form.brand_parknshop.data)
    user.brand_watsons = bool(form.brand_watsons.data)
    user.brand_moneyback = bool(form.brand_moneyback.data)

    unit = (form.addr_unit.data or '').strip()
    floor = (form.addr_floor.data or '').strip()
    building = (form.addr_building_street.data or '').strip()
    region = (form.addr_region.data or '').strip()
    district = (form.addr_district.data or '').strip()
    home_ph = (form.home_phone.data or '').strip()

    has_addr = any([unit, floor, building, region, district, home_ph])
    existing_addrs = user.addresses.order_by(UserAddress.create_time.asc()).all()
    addr = next((a for a in existing_addrs if a.is_default), None) or (existing_addrs[0] if existing_addrs else None)

    if not has_addr:
        if addr:
            db.session.delete(addr)
            # 刪除預設地址後，若仍有其他地址，接續預設
            remaining = [a for a in existing_addrs if a.user_address_uuid != addr.user_address_uuid]
            if remaining:
                for a in remaining:
                    a.is_default = False
                remaining[0].is_default = True
        return

    line = ' '.join(x for x in [region, district, building, floor, unit] if x).strip() or '-'

    if not addr:
        addr = UserAddress(user_uuid=user.user_uuid, user_address=line)
        db.session.add(addr)
    else:
        addr.user_address = line

    # 個人資料頁的「送貨地址」視為預設地址：清掉其他預設標記，並標記目前 addr
    for a in existing_addrs:
        a.is_default = False
    addr.is_default = True

    addr.unit = unit or None
    addr.floor = floor or None
    addr.building_street = building or None
    addr.region = region or None
    addr.district = district or None
    addr.home_phone = home_ph or None
    sync_ph = (user.phone_number or '').strip()
    addr.phone_number = sync_ph if sync_ph else None


def _clear_reg_session():
    for k in (
        'reg_pending_user_name',
        'reg_pending_mail',
        'reg_password_hash',
        'reg_password_plain',
        'reg_email_verified',
        'reg_verify_code',
        'reg_verify_exp',
        'reg_verify_row_id',
        'verify_code_input_error',
    ):
        session.pop(k, None)


def _reg_extra_session_ok():
    """第三步：已完成郵箱驗證且 session 仍帶有註冊資料。"""
    return bool(
        session.get('reg_email_verified')
        and session.get('reg_pending_user_name')
        and session.get('reg_pending_mail')
        and session.get('reg_password_hash')
    )


def _mask_email(mail):
    if not mail or '@' not in mail:
        return mail or ''
    local, _, domain = mail.partition('@')
    if len(local) <= 1:
        return f'*@{domain}'
    return f'{local[0]}***@{domain}'


def _client_ip():
    xff = (request.headers.get('X-Forwarded-For') or '').strip()
    if xff:
        return xff.split(',')[0].strip()
    return (request.remote_addr or '0.0.0.0').strip()


def _ip_window_pending_registration_row(ip):
    """同一 IP 在 15 分鐘內、尚未完成註冊的驗證碼記錄（若有則可複用寄送同一組碼）。"""
    window_start = datetime.now(timezone.utc) - timedelta(minutes=REG_VERIFY_IP_COOLDOWN_MIN)
    return (
        RegistrationVerificationCode.query.filter(
            RegistrationVerificationCode.client_ip == ip,
            RegistrationVerificationCode.consumed_at.is_(None),
            RegistrationVerificationCode.created_at >= window_start,
        )
        .order_by(RegistrationVerificationCode.created_at.desc())
        .first()
    )


def _delete_registration_code_row(row_id):
    if not row_id:
        return
    row = db.session.get(RegistrationVerificationCode, row_id)
    if row:
        db.session.delete(row)
        db.session.commit()


def _registration_verify_fail_flash_message(row, pending_mail):
    if not pending_mail:
        return '請先填寫註冊資料或工作階段已過期。'
    if row is None:
        return '請先填寫註冊資料或工作階段已過期。'
    if (row.mail or '').strip().lower() != pending_mail.lower():
        return '驗證資料與工作階段不符，請重新註冊。'
    if row.consumed_at is not None:
        return '驗證資料與工作階段不符，請重新註冊。'
    if datetime.now(timezone.utc) > row.expires_at:
        return '驗證碼已過期，請重新註冊。'
    return None


def _pending_registration_verification_row():
    """回傳 (pending_mail, row, error_message)；error_message 為 None 表示可繼續。"""
    pending_mail = (session.get('reg_pending_mail') or '').strip()
    if not pending_mail:
        return None, None, '請先填寫註冊資料或工作階段已過期。'
    row_id = session.get('reg_verify_row_id')
    row = db.session.get(RegistrationVerificationCode, row_id) if row_id else None
    return pending_mail, row, _registration_verify_fail_flash_message(row, pending_mail)


def _issue_registration_code(mail):
    code = f'{secrets.randbelow(1_000_000):06d}'
    now = datetime.now(timezone.utc)
    expires = now + timedelta(seconds=REG_VERIFY_TTL_SEC)
    row = RegistrationVerificationCode(
        client_ip=_client_ip(),
        code=code,
        mail=mail,
        created_at=now,
        expires_at=expires,
        last_sent_at=now,
    )
    db.session.add(row)
    db.session.commit()
    session['reg_verify_code'] = code
    session['reg_verify_exp'] = time.time() + REG_VERIFY_TTL_SEC
    session['reg_verify_row_id'] = row.id
    return code


def _send_reg_code_or_flash(mail, user_name, code):
    try:
        send_registration_verification_email(mail, user_name, code)
    except RuntimeError as e:
        flash(str(e))
        return False
    except Exception as e:
        app.logger.exception('註冊驗證郵件發送失敗')
        if app.debug:
            flash(f'[開發] SMTP 錯誤：{e!s}')
            flash(f'[開發] 驗證碼：{code}（可先手動輸入測試）')
            return True
        flash('驗證郵件發送失敗，請稍後再試。若持續失敗，請確認 .env 內 MAIL_PASSWORD 與信箱設定。')
        return False
    return True


@app.template_global()
def browse_url(section, slug):
    return url_for('category_browse', section=section, slug=slug)


@app.template_global()
def product_image_url(image_path):
    if not image_path:
        return ''
    s = str(image_path).strip()
    if s.startswith('http://') or s.startswith('https://'):
        return s
    return url_for('static', filename=s)


@app.context_processor
def inject_maternity_nav():
    try:
        from app.maternity_nav import build_maternity_mega_nav

        return {'maternity_nav': build_maternity_mega_nav()}
    except Exception:
        app.logger.exception('母嬰導航載入失敗')
        return {'maternity_nav': None}


@app.before_request
def before_request():
    g.locale = str(get_locale())


@app.route('/catalog/category/<int:category_id>', methods=['GET'])
def catalog_category(category_id):
    cat = db.session.get(ProductCategory, category_id)
    if cat is None:
        abort(404)

    supplier_id = request.args.get('supplier_id', type=int)

    chain: list[ProductCategory] = []
    node: ProductCategory | None = cat
    while node is not None:
        chain.append(node)
        pid = node.parent_id
        node = db.session.get(ProductCategory, pid) if pid is not None else None
    chain.reverse()

    breadcrumbs = [{'label': _('首頁'), 'url': url_for('index')}]
    for i, c in enumerate(chain):
        last = i == len(chain) - 1
        breadcrumbs.append(
            {
                'label': c.product_categories_name,
                'url': None if last else url_for('catalog_category', category_id=c.product_categories_id),
            }
        )

    q = ProductDetail.query.filter(ProductDetail.product_categories_id == category_id)
    if supplier_id is not None:
        q = q.filter(ProductDetail.supplier_id == supplier_id)
    rows = q.order_by(ProductDetail.product_name.asc()).limit(120).all()

    products = []
    for i, p in enumerate(rows):
        img = product_image_url(p.image_path)
        products.append(
            {
                'name': p.product_name,
                'unit': p.specification or '',
                'price': float(p.price),
                'discount_price': float(p.discount_price) if p.discount_price is not None else None,
                'img_mod': (i % 8) + 1,
                'image_url': img,
            }
        )

    title = f'{cat.product_categories_name} - PNS'
    filter_note = ''
    if supplier_id is not None:
        filter_note = _('（已依品牌篩選）')

    return render_template(
        'catalog_category.html.j2',
        title=title,
        browse_title=cat.product_categories_name,
        browse_description=_('此分類從資料庫載入的商品。') + filter_note,
        breadcrumbs=breadcrumbs,
        products=products,
        supplier_id=supplier_id,
        category_id=category_id,
    )


@app.route('/browse/<section>/<slug>', methods=['GET'])
def category_browse(section, slug):
    ctx = build_browse_page(section, slug)
    if ctx is None:
        abort(404)
    return render_template('category_browse.html.j2', **ctx)


@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    if current_user.is_anonymous:
        return render_template('index.html.j2', title=_('PNS 網購'))
    return render_template(
        'index.html.j2',
        title=_('Home'),
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if request.method == 'GET':
        u = session.pop('login_prefill_username', None)
        p = session.pop('login_prefill_password', None)
        if u is not None:
            form.username.data = u
        if p is not None:
            form.password.data = p
    if form.validate_on_submit():
        raw = (form.username.data or '').strip()
        user = User.query.filter(
            or_(
                User.user_name == raw,
                func.lower(User.mail) == raw.lower(),
            )
        ).first()
        if user is None or not user.check_password(form.password.data):
            flash('使用者名稱、電子郵件或密碼不正確')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html.j2', title='登入', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'GET':
        _clear_reg_session()
    form = RegistrationForm()
    if form.validate_on_submit():
        ip = _client_ip()
        pending_user = form.username.data.strip()
        pending_mail = form.email.data.strip()
        pw_hash = generate_password_hash(form.password.data)
        pw_plain = form.password.data
        now = datetime.now(timezone.utc)

        existing = _ip_window_pending_registration_row(ip)
        if existing is not None and (existing.mail or '').strip().lower() != pending_mail.lower():
            flash(
                '此 IP 15 分鐘內已有未完成的註冊驗證，請使用原註冊信箱 '
                f'（{_mask_email(existing.mail)}）或稍後再試。'
            )
            return redirect(url_for('register'))

        session['reg_pending_user_name'] = pending_user
        session['reg_pending_mail'] = pending_mail
        session['reg_password_hash'] = pw_hash
        session['reg_password_plain'] = pw_plain

        if existing is None:
            code = _issue_registration_code(pending_mail)
            if not _send_reg_code_or_flash(
                pending_mail,
                pending_user,
                code,
            ):
                _delete_registration_code_row(session.get('reg_verify_row_id'))
                _clear_reg_session()
                return redirect(url_for('register'))
            flash('驗證碼已發送至您的信箱，請查收。')
            return redirect(url_for('register_verify'))

        if existing.expires_at < now:
            db.session.delete(existing)
            db.session.commit()
            code = _issue_registration_code(pending_mail)
            if not _send_reg_code_or_flash(
                pending_mail,
                pending_user,
                code,
            ):
                _delete_registration_code_row(session.get('reg_verify_row_id'))
                _clear_reg_session()
                return redirect(url_for('register'))
            flash('驗證碼已發送至您的信箱，請查收。')
            return redirect(url_for('register_verify'))

        session['reg_verify_code'] = existing.code
        session['reg_verify_exp'] = existing.expires_at.timestamp()
        session['reg_verify_row_id'] = existing.id
        if not _send_reg_code_or_flash(
            pending_mail,
            pending_user,
            existing.code,
        ):
            return redirect(url_for('register_verify'))
        existing.last_sent_at = now
        db.session.commit()
        flash('驗證碼已發送至您的信箱，請查收。')
        return redirect(url_for('register_verify'))
    return render_template('register.html.j2', title='註冊', form=form)


@app.route('/register/verify', methods=['GET', 'POST'])
def register_verify():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    pending_mail, row, err = _pending_registration_verification_row()
    if err:
        flash(err)
        _clear_reg_session()
        return redirect(url_for('register'))
    form = EmailVerificationForm()
    resend_form = ResendVerifyForm()
    if form.validate_on_submit():
        row = db.session.get(RegistrationVerificationCode, session.get('reg_verify_row_id'))
        err = _registration_verify_fail_flash_message(row, pending_mail)
        if err:
            flash(err)
            _clear_reg_session()
            return redirect(url_for('register'))
        submitted = (form.code.data or '').strip()
        if submitted != row.code:
            flash('驗證碼不正確，請再試一次。')
            session['verify_code_input_error'] = True
            return redirect(url_for('register_verify'))
        row.consumed_at = datetime.now(timezone.utc)
        db.session.commit()
        session['reg_email_verified'] = True
        for k in ('reg_verify_code', 'reg_verify_exp', 'reg_verify_row_id', 'verify_code_input_error'):
            session.pop(k, None)
        flash('郵箱已驗證，請填寫聯絡資料。')
        return redirect(url_for('register_extra'))
    if request.method == 'POST' and form.is_submitted():
        if form.errors.get('code'):
            flash(form.code.errors[0])
            session['verify_code_input_error'] = True
        return redirect(url_for('register_verify'))
    masked_email = _mask_email(session['reg_pending_mail'])
    code_input_error = session.pop('verify_code_input_error', False)
    return render_template(
        'register_verify.html.j2',
        title='驗證郵箱',
        form=form,
        resend_form=resend_form,
        masked_email=masked_email,
        code_input_error=code_input_error,
    )


@app.route('/register/extra', methods=['GET', 'POST'])
def register_extra():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if not _reg_extra_session_ok():
        flash('請先完成註冊前兩步驟。')
        return redirect(url_for('register'))
    form = RegisterExtraForm()
    if form.validate_on_submit():
        user = User(
            user_name=session['reg_pending_user_name'],
            mail=session['reg_pending_mail'],
            phone_number=form.phone.data.strip(),
        )
        user.password_hash = session['reg_password_hash']
        db.session.add(user)
        db.session.flush()
        addr_text = (form.address.data or '').strip()
        if addr_text:
            db.session.add(
                UserAddress(
                    user_uuid=user.user_uuid,
                    user_address=addr_text,
                )
            )
        db.session.add(Membership(user_uuid=user.user_uuid, membership_point=0))
        db.session.commit()
        pref_user = session['reg_pending_user_name']
        pref_pw = session.pop('reg_password_plain', None)
        _clear_reg_session()
        session['login_prefill_username'] = pref_user
        if pref_pw is not None:
            session['login_prefill_password'] = pref_pw
        flash('註冊成功，請登入。')
        return redirect(url_for('login'))
    return render_template('register_extra.html.j2', title='聯絡資料', form=form)


@app.route('/register/verify/resend', methods=['POST'])
def register_verify_resend():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    resend_form = ResendVerifyForm()
    if not resend_form.validate_on_submit():
        return redirect(url_for('register_verify'))
    pending_mail, row, err = _pending_registration_verification_row()
    if err:
        flash(err)
        _clear_reg_session()
        return redirect(url_for('register'))
    code = row.code
    if not _send_reg_code_or_flash(
        session['reg_pending_mail'],
        session['reg_pending_user_name'],
        code,
    ):
        return redirect(url_for('register_verify'))
    row.last_sent_at = datetime.now(timezone.utc)
    db.session.commit()
    flash('已重新發送驗證郵件。')
    return redirect(url_for('register_verify'))


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(mail=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(
            '若該信箱已註冊，您將收到重設密碼的電子郵件，請依信內指示操作。')
        return redirect(url_for('login'))
    return render_template(
        'reset_password_request.html.j2',
        title='忘記密碼',
        form=form,
    )


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if user is None:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('密碼已重設，請使用新密碼登入。')
        return redirect(url_for('login'))
    return render_template(
        'reset_password.html.j2',
        title='重設密碼',
        form=form,
    )


@app.route('/user/<username>')
@login_required
def user(username):
    profile_user = User.query.filter_by(user_name=username).first_or_404()
    return render_template('user.html.j2', user=profile_user)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.user_name, current_user.mail)
    if request.method == 'POST':
        reg = (request.form.get('addr_region') or '').strip()
        if reg in HK_DISTRICTS:
            form.addr_district.choices = [('', '請選擇')] + [(d, d) for d in HK_DISTRICTS[reg]]
    if form.validate_on_submit():
        _save_profile_and_address(form, current_user)
        db.session.commit()
        flash('資料已儲存。')
        return redirect(url_for('edit_profile'))
    if request.method == 'GET':
        _populate_edit_profile_form(form, current_user)
    return render_template(
        'partials/info-page_edit-profile.html.j2',
        title='個人資料',
        form=form,
        hk_districts=HK_DISTRICTS,
        addresses=current_user.addresses.order_by(UserAddress.create_time.desc()).all(),
    )


@app.route('/delivery_address', methods=['GET'])
@login_required
def delivery_address():
    addresses = current_user.addresses.order_by(UserAddress.create_time.desc()).all()
    if addresses:
        defaults = [a for a in addresses if a.is_default]
        # 舊資料可能沒有預設、或不小心出現多個預設：兜底保證只保留一筆
        if len(defaults) != 1:
            for a in addresses:
                a.is_default = False
            addresses[0].is_default = True
            db.session.commit()
    form = DeliveryAddressForm()
    form.home_phone.data = (current_user.phone_number or '').strip()
    return render_template(
        'partials/info-page_delivery-address.html.j2',
        title='送貨地址',
        addresses=addresses,
        form=form,
        hk_districts=HK_DISTRICTS,
    )


@app.route('/membership_points', methods=['GET'])
@login_required
def membership_points():
    membership = current_user.membership_row
    if membership is None:
        membership = Membership(user_uuid=current_user.user_uuid, membership_point=0)
        db.session.add(membership)
        db.session.commit()

    logs = current_user.points_logs.order_by(MembershipPointsLog.transaction_time.desc()).all()
    hkd_equivalent = int(membership.membership_point // 50)
    expiring_points = min(membership.membership_point, 93)
    expiry_date = datetime(2027, 10, 1)

    return render_template(
        'partials/info-page_membership-points.html.j2',
        title='易賞錢積分',
        membership=membership,
        points_logs=logs,
        hkd_equivalent=hkd_equivalent,
        expiring_points=expiring_points,
        expiry_date=expiry_date,
    )


@app.route('/digital_coupons', methods=['GET'])
@login_required
def digital_coupons():
    return render_template(
        'partials/info-page_digital-coupons.html.j2',
        title='電子優惠券／電子禮券',
    )


@app.route('/my_credit_cards', methods=['GET'])
@login_required
def my_credit_cards():
    return render_template(
        'partials/info-page_credit-cards.html.j2',
        title='我的信用卡',
    )


@app.route('/delivery_address/add', methods=['POST'])
@login_required
def delivery_address_add():
    form = DeliveryAddressForm()
    if form.validate_on_submit():
        unit = (form.addr_unit.data or '').strip()
        floor = (form.addr_floor.data or '').strip()
        building = (form.addr_building_street.data or '').strip()
        region = (form.addr_region.data or '').strip()
        district = (form.addr_district.data or '').strip()
        home_phone = (form.home_phone.data or '').strip()
        home_tel = (form.home_tel.data or '').strip()

        line = ' '.join(
            x for x in [region, district, building, floor, unit] if x
        ).strip() or '-'

        addr = UserAddress(
            user_uuid=current_user.user_uuid,
            user_address=line,
            unit=unit or None,
            floor=floor or None,
            building_street=building or None,
            region=region or None,
            district=district or None,
            phone_number=home_phone or None,
            home_phone=home_tel or None,
        )

        existing_count = current_user.addresses.count()
        has_default = current_user.addresses.filter(UserAddress.is_default.is_(True)).count() > 0
        # 第一個地址預設為預設地址；若舊資料沒有預設標記，新增後自動設為預設
        if existing_count == 0 or not has_default:
            addr.is_default = True

        db.session.add(addr)
        db.session.commit()
        flash('地址已儲存。')
        return redirect(url_for('delivery_address'))

    flash('請檢查輸入資料。')
    return redirect(url_for('delivery_address'))


@app.route('/delivery_address/set_default/<user_address_uuid>', methods=['GET'])
@login_required
def delivery_address_set_default(user_address_uuid):
    # 僅允許設定為自己的地址
    addresses = current_user.addresses.all()
    target = None
    for a in addresses:
        if str(a.user_address_uuid) == str(user_address_uuid):
            target = a
            break
    if target is None:
        return redirect(url_for('delivery_address'))

    for a in addresses:
        a.is_default = False
    target.is_default = True
    db.session.commit()
    flash('已設定預設送貨地址。')
    return redirect(url_for('delivery_address'))


@app.route('/delivery_address/delete/<user_address_uuid>', methods=['GET'])
@login_required
def delivery_address_delete(user_address_uuid):
    addresses = current_user.addresses.order_by(UserAddress.create_time.desc()).all()
    target = None
    for a in addresses:
        if str(a.user_address_uuid) == str(user_address_uuid):
            target = a
            break
    if target is None:
        return redirect(url_for('delivery_address'))

    was_default = bool(target.is_default)
    db.session.delete(target)
    db.session.flush()

    remaining = current_user.addresses.order_by(UserAddress.create_time.desc()).all()
    if remaining and (was_default or not any(a.is_default for a in remaining)):
        for a in remaining:
            a.is_default = False
        remaining[0].is_default = True

    db.session.commit()
    flash('地址已刪除。')
    return redirect(url_for('delivery_address'))
