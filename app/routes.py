import os
import random
import re
import secrets
import time
import uuid
from decimal import Decimal, ROUND_DOWN
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from collections import defaultdict

from sqlalchemy import func, or_, inspect
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash

from flask import (
    render_template,
    flash,
    redirect,
    url_for,
    request,
    g,
    session,
    abort,
    current_app,
    jsonify,
)
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
    OrderRefundForm,
    ProductReviewForm,
)
from app.models import (
    User,
    UserAddress,
    Membership,
    MembershipPointsLog,
    RegistrationVerificationCode,
    ProductCategory,
    ProductDetail,
    Supplier,
    Cart,
    Order,
    OrderItem,
    Delivery,
    PaymentLog,
    Refund,
    Evaluate,
)
from app.category_catalog import build_browse_page
from app.maternity_nav import _collect_descendant_category_ids
from app.email import send_password_reset_email, send_registration_verification_email
from app.hk_address import HK_DISTRICTS


REG_VERIFY_TTL_SEC = 900
REG_VERIFY_IP_COOLDOWN_MIN = 15
REG_VERIFY_IP_MAX_PENDING = 3
POINTS_EARN_HKD_RATE = Decimal('10')
POINTS_TO_HKD_RATE = Decimal('50')
POINTS_LOG_RETAILER = '易賞錢'
POINTS_LOG_ORDER_PREFIX = '網上訂單 #'
POINTS_LOG_REFUND_PREFIX = '訂單退款 #'
DEFAULT_POINTS_EXPIRY_DATE = datetime(2027, 10, 1)
DEFAULT_E_STAMPS = (
    {
        'title': '花王電子印花',
        'image': 'png/account/PNS-x-KAO-PNS-Estamp-202503-v1.avif',
        'date_range': '2025/05/01 - 2026/03/31',
    },
    {
        'title': '網購店取即日取貨',
        'image': 'png/account/Asset-1.png',
        'date_range': '2025/11/14 - 2026/12/31',
    },
    {
        'title': 'Staub 電子印花',
        'image': 'png/account/Staub-x-Ballarini-Mass-eStamp-1-.avif',
        'date_range': '2026/01/09 - 2026/04/23',
    },
)
DELIVERY_SLOT_CHOICES = (
    ('morning', '早上'),
    ('afternoon', '下午'),
    ('evening', '晚上'),
)
DELIVERY_SLOT_HOURS = {
    'morning': 9,
    'afternoon': 14,
    'evening': 19,
}


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


def _get_or_create_membership(user):
    membership = user.membership_row
    if membership is None:
        membership = Membership(user_uuid=user.user_uuid, membership_point=0)
        db.session.add(membership)
    return membership


def _build_points_summary(membership):
    points = int(membership.membership_point or 0)
    return {
        'points': points,
        'hkd_equivalent': float((Decimal(points) / POINTS_TO_HKD_RATE).quantize(Decimal('0.01'))),
        'expiring_points': min(points, 93),
        'expiry_date': DEFAULT_POINTS_EXPIRY_DATE,
    }


def _order_code(order):
    return str(order.order_uuid).split('-')[0].upper()


def _points_order_store_name(order):
    return f'{POINTS_LOG_ORDER_PREFIX}{_order_code(order)}'


def _points_refund_store_name(order):
    return f'{POINTS_LOG_REFUND_PREFIX}{_order_code(order)}'


def _calculate_earned_points(amount_hkd):
    amount = Decimal(str(amount_hkd or 0))
    return int((amount / POINTS_EARN_HKD_RATE).to_integral_value(rounding=ROUND_DOWN))


def _points_delta_from_log(log):
    return int(log.base_points or 0) + int(log.extra_points or 0) - int(log.redeemed_points or 0)


def _is_refunded_order(order):
    return (order.order_status or '').strip().lower() in ('refund', 'refunded', '退款')


def _is_points_eligible_order(order):
    return (order.order_status or '').strip().lower() in ('paid', 'refund', 'refunded', '退款')


def _build_points_log_timestamp(value):
    return value if value is not None else datetime.utcnow()


def _safe_internal_redirect_target(value, fallback_endpoint='index'):
    target = (value or '').strip()
    if not target:
        return url_for(fallback_endpoint)
    parsed = urlparse(target)
    if parsed.netloc or parsed.scheme:
        return url_for(fallback_endpoint)
    if not target.startswith('/') or target.startswith('//'):
        return url_for(fallback_endpoint)
    return target


def _delivery_slot_label(slot):
    mapping = {key: _(label) for key, label in DELIVERY_SLOT_CHOICES}
    return mapping.get((slot or '').strip(), '')


def _delivery_slot_anchor_text(slot):
    normalized_slot = (slot or '').strip()
    hour = DELIVERY_SLOT_HOURS.get(normalized_slot)
    if hour is None:
        return ''
    return f'{hour:02d}:00'


def _delivery_slot_choices():
    return [
        {
            'value': key,
            'label': f"{_(label)} ({_delivery_slot_anchor_text(key)})",
        }
        for key, label in DELIVERY_SLOT_CHOICES
    ]


def _build_delivery_time(slot, base_dt=None):
    normalized_slot = (slot or '').strip()
    hour = DELIVERY_SLOT_HOURS.get(normalized_slot)
    if hour is None:
        return None
    base = base_dt or datetime.utcnow()
    return datetime(base.year, base.month, base.day, hour, 0, 0)


def _delivery_time_label(deliver_time):
    if deliver_time is None:
        return ''
    return f'{int(deliver_time.hour or 0):02d}:{int(deliver_time.minute or 0):02d}'


def _sync_membership_points(user, membership=None, commit=False):
    membership = membership or _get_or_create_membership(user)
    feature_tables = _order_feature_tables_state()
    existing_logs = user.points_logs.order_by(MembershipPointsLog.transaction_time.asc()).all()
    logs_by_key = {
        ((log.retailer or '').strip(), (log.store_name or '').strip()): log
        for log in existing_logs
    }
    changed = membership in db.session.new

    for order in user.orders.order_by(Order.create_time.asc()).all():
        if not _is_points_eligible_order(order):
            continue
        earned_points = _calculate_earned_points(order.total_price)
        if earned_points <= 0:
            continue

        earn_store_name = _points_order_store_name(order)
        earn_key = (POINTS_LOG_RETAILER, earn_store_name)
        if earn_key not in logs_by_key:
            earn_log = MembershipPointsLog(
                user_uuid=user.user_uuid,
                transaction_time=_build_points_log_timestamp(order.create_time),
                retailer=POINTS_LOG_RETAILER,
                store_name=earn_store_name,
                transaction_amount_hkd=order.total_price or 0,
                base_points=earned_points,
                extra_points=0,
                redeemed_points=None,
            )
            db.session.add(earn_log)
            existing_logs.append(earn_log)
            logs_by_key[earn_key] = earn_log
            changed = True

        if feature_tables['refund'] and _is_refunded_order(order):
            refund_store_name = _points_refund_store_name(order)
            refund_key = (POINTS_LOG_RETAILER, refund_store_name)
            if refund_key not in logs_by_key:
                refund_row = order.refunds.order_by(Refund.create_time.asc()).first()
                refund_log = MembershipPointsLog(
                    user_uuid=user.user_uuid,
                    transaction_time=_build_points_log_timestamp(
                        refund_row.create_time if refund_row is not None else None
                    ),
                    retailer=POINTS_LOG_RETAILER,
                    store_name=refund_store_name,
                    transaction_amount_hkd=order.total_price or 0,
                    base_points=0,
                    extra_points=0,
                    redeemed_points=earned_points,
                )
                db.session.add(refund_log)
                existing_logs.append(refund_log)
                logs_by_key[refund_key] = refund_log
                changed = True

    computed_points = max(sum(_points_delta_from_log(log) for log in existing_logs), 0)
    if int(membership.membership_point or 0) != computed_points:
        membership.membership_point = computed_points
        changed = True

    if changed and commit:
        db.session.commit()

    logs = sorted(
        existing_logs,
        key=lambda log: (log.transaction_time or log.create_time or datetime.min),
        reverse=True,
    )
    return membership, logs, _build_points_summary(membership)


def _cleanup_refunded_reviews(user, commit=False):
    feature_tables = _order_feature_tables_state()
    if not feature_tables['evaluate'] or not feature_tables['refund']:
        return False

    refunded_product_ids = {
        item.product_details_uuid
        for order in user.orders.order_by(Order.create_time.asc()).all()
        if _is_refunded_order(order)
        for item in order.items.order_by(OrderItem.create_time.asc()).all()
        if item.product_details_uuid is not None
    }
    if not refunded_product_ids:
        return False

    reviews = (
        Evaluate.query.filter(
            Evaluate.user_uuid == user.user_uuid,
            Evaluate.product_details_uuid.in_(refunded_product_ids),
        ).all()
    )
    if not reviews:
        return False

    for review in reviews:
        db.session.delete(review)

    if commit:
        db.session.commit()
    return True


def _build_dashboard_stamps():
    return [
        {
            'title': _(stamp['title']),
            'image': stamp['image'],
            'date_range': stamp['date_range'],
            'count': 0,
        }
        for stamp in DEFAULT_E_STAMPS
    ]


def _build_recent_purchase_items(user, limit=3):
    rows = (
        OrderItem.query.options(joinedload(OrderItem.order), joinedload(OrderItem.product))
        .join(Order, Order.order_uuid == OrderItem.order_uuid)
        .filter(
            Order.user_uuid == user.user_uuid,
            Order.order_status == 'paid',
        )
        .order_by(Order.create_time.desc(), OrderItem.create_time.desc())
        .limit(limit)
        .all()
    )

    items = []
    for row in rows:
        product = row.product
        order = row.order
        items.append(
            {
                'product_uuid': str(row.product_details_uuid) if row.product_details_uuid is not None else '',
                'product_name': ((product.product_name if product else '') or _('商品')).strip(),
                'image_url': product_image_url(product.image_path) if product and product.image_path else '',
                'quantity': int(row.quantity or 0),
                'line_total': float(row.line_total or 0),
                'order_code': _order_code(order) if order is not None else '',
                'order_created_at': order.create_time if order is not None else None,
            }
        )
    return items


def _build_product_review_cards(user):
    reviews = (
        Evaluate.query.options(
            joinedload(Evaluate.product).joinedload(ProductDetail.supplier),
        )
        .filter(Evaluate.user_uuid == user.user_uuid)
        .order_by(Evaluate.create_time.desc())
        .all()
    )

    category_ids = {
        product.product_categories_id
        for product in (review.product for review in reviews)
        if product is not None and product.product_categories_id is not None
    }
    category_names = {
        row.product_categories_id: (row.product_categories_name or '').strip()
        for row in ProductCategory.query.filter(ProductCategory.product_categories_id.in_(category_ids)).all()
    } if category_ids else {}

    latest_order_items = (
        OrderItem.query.options(joinedload(OrderItem.order))
        .join(Order, Order.order_uuid == OrderItem.order_uuid)
        .filter(Order.user_uuid == user.user_uuid)
        .order_by(Order.create_time.desc(), OrderItem.create_time.desc())
        .all()
    )

    latest_order_by_product = {}
    for item in latest_order_items:
        latest_order_by_product.setdefault(item.product_details_uuid, item)

    cards = []
    for review in reviews:
        product = review.product
        product_name = _('商品')
        category_name = ''
        specification = ''
        image_url = ''
        catalog_url = ''

        if product is not None:
            supplier_name = ((product.supplier.supplier_name if product.supplier is not None else '') or '').strip()
            base_name = (product.product_name or '').strip()
            product_name = f'{supplier_name} {base_name}'.strip() if supplier_name else (base_name or _('商品'))
            category_name = category_names.get(product.product_categories_id, '')
            specification = (product.specification or '').strip()
            image_url = product_image_url(product.image_path) if product.image_path else ''
            if product.product_categories_id is not None:
                catalog_url = url_for('catalog_category', category_id=product.product_categories_id)

        order_item = latest_order_by_product.get(review.product_details_uuid)
        order = order_item.order if order_item is not None else None

        cards.append(
            {
                'product_name': product_name,
                'category_name': category_name,
                'specification': specification,
                'image_url': image_url,
                'catalog_url': catalog_url,
                'review_text': ((review.evalate_txt or '').strip() or _('尚未填寫評論內容')),
                'review_created_at': review.create_time,
                'purchase_created_at': order.create_time if order is not None else None,
                'order_code': str(order.order_uuid).split('-')[0].upper() if order is not None else '',
                'quantity': int(order_item.quantity or 0) if order_item is not None else None,
                'paid_price': float(order_item.line_total or 0) if order_item is not None else None,
            }
        )

    return {
        'cards': cards,
        'count': len(cards),
        'latest_review_at': reviews[0].create_time if reviews else None,
    }


def _display_order_status(status):
    raw = (status or '').strip().lower()
    if raw == 'paid':
        return _('已付款')
    if raw in ('refund', 'refunded', '退款'):
        return _('退款')
    return status or _('未知')


def _order_feature_tables_state():
    inspector = inspect(db.engine)
    return {
        'delivery': inspector.has_table('delivery'),
        'payment_log': inspector.has_table('payment_log'),
        'refund': inspector.has_table('refund'),
        'evaluate': inspector.has_table('evaluate'),
    }


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


def _ip_window_pending_registration_rows(ip):
    """同一 IP 在 15 分鐘內、尚未完成註冊的驗證碼記錄。"""
    window_start = datetime.now(timezone.utc) - timedelta(minutes=REG_VERIFY_IP_COOLDOWN_MIN)
    return (
        RegistrationVerificationCode.query.filter(
            RegistrationVerificationCode.client_ip == ip,
            RegistrationVerificationCode.consumed_at.is_(None),
            RegistrationVerificationCode.created_at >= window_start,
        )
        .order_by(RegistrationVerificationCode.created_at.desc())
        .all()
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


@app.context_processor
def inject_cart_count():
    cart_count = 0
    if current_user.is_authenticated:
        cart_count = Cart.query.filter_by(user_uuid=current_user.user_uuid).count()
    else:
        # For anonymous users, count items in session
        cart_items = session.get('cart', {})
        cart_count = sum(cart_items.values())
    return {'cart_count': cart_count}


@app.template_global()
def product_image_url(image_path):
    if not image_path:
        return ''
    s = str(image_path).strip()
    if s.startswith('http://') or s.startswith('https://'):
        return s
    return url_for('static', filename=s.lstrip('/'))


def _static_product_image_file_exists(rel_path: str) -> bool:
    root = current_app.static_folder
    if not root or not rel_path:
        return False
    rel = str(rel_path).strip().lstrip('/')
    if not rel or rel.startswith('..'):
        return False
    full = os.path.normpath(os.path.join(root, rel))
    root_norm = os.path.normpath(root)
    if not full.startswith(root_norm + os.sep) and full != root_norm:
        return False
    return os.path.isfile(full)


def _promo_image_will_display(image_path) -> bool:
    """遠端 URL 或可找到的 static 檔案，避免首頁出現破圖或空白圖。"""
    if image_path is None:
        return False
    s = str(image_path).strip()
    if not s:
        return False
    if s.startswith('http://') or s.startswith('https://'):
        return True
    return _static_product_image_file_exists(s)


HOME_NEW_ARRIVALS_SCAN_LIMIT = 120
HOME_NEW_ARRIVALS_DISPLAY = 4
HOME_PROMO_DEALS_SCAN_LIMIT = 120
HOME_PROMO_DEALS_DISPLAY = 4
HOME_DISCOUNT_SHELF_DISPLAY = 6
HOME_FOCUS_RECOMMENDATIONS_DISPLAY = 6
HOME_CASE_DEAL_SCAN_LIMIT = 240
HOME_CASE_DEAL_DISPLAY = 6
HOME_GENERIC_SHELF_SCAN_LIMIT = 1000
HOME_GENERIC_SHELF_KEYS = (
    'meow9',
    'easter',
    'fitness',
    'xinjiapin',
    'duomai',
    'maihaozhuan',
    'xingzhijiapin',
    'huanqiu_xianrou',
    'xiansong_xiande',
)


def _product_detail_to_promo_card(p: ProductDetail) -> dict:
    img = product_image_url(p.image_path)
    brand = (p.supplier.supplier_name if p.supplier is not None else '') or ''
    brand = brand.strip()
    pname = (p.product_name or '').strip()
    display_name = f'{brand} {pname}'.strip() if brand else pname
    price_f = float(p.price)
    disc = p.discount_price
    disc_f = float(disc) if disc is not None else None
    return {
        'uuid': str(p.product_categories_uuid),
        'name': display_name or _('商品'),
        'image_url': img,
        'price': price_f,
        'discount_price': disc_f,
        'catalog_url': url_for('catalog_category', category_id=p.product_categories_id),
    }


def _product_detail_to_shelf_card(p: ProductDetail) -> dict:
    img = product_image_url(p.image_path)
    brand = (p.supplier.supplier_name if p.supplier is not None else '') or ''
    brand = brand.strip()
    pname = (p.product_name or '').strip()
    display_name = f'{brand} {pname}'.strip() if brand else pname
    discount_price = float(p.discount_price) if p.discount_price is not None else None
    original_price = float(p.price)
    return {
        'uuid': str(p.product_categories_uuid),
        'name': display_name or _('商品'),
        'spec': (p.specification or '').strip(),
        'sale_price': discount_price if discount_price is not None else original_price,
        'original_price': original_price if discount_price is not None else None,
        'image_url': img,
    }


def _is_case_deal_candidate(p: ProductDetail) -> bool:
    haystack = ' '.join(
        [
            (p.product_name or '').strip(),
            (p.specification or '').strip(),
        ]
    ).lower()
    keyword_hits = ('原箱', '整箱', '箱裝', '箱装', 'case', 'carton', 'pack')
    if any(keyword in haystack for keyword in keyword_hits):
        return True
    if re.search(r'\d+\s*[xX]\s*\d+\s*[xX]\s*\d+', haystack):
        return True
    return False


def _format_sales_count_label(quantity: int) -> str:
    qty = max(int(quantity or 0), 0)
    if qty >= 1000:
        return _('已售 %(count)sK+', count=f'{qty / 1000:.1f}'.rstrip('0').rstrip('.'))
    return _('已售 %(count)s', count=qty)


def _product_detail_to_focus_card(p: ProductDetail, sold_qty: int) -> dict:
    img = product_image_url(p.image_path)
    brand = (p.supplier.supplier_name if p.supplier is not None else '') or ''
    brand = brand.strip()
    pname = (p.product_name or '').strip()
    display_name = f'{brand} {pname}'.strip() if brand else pname
    price_f = float(p.price)
    disc = p.discount_price
    disc_f = float(disc) if disc is not None else None
    return {
        'uuid': str(p.product_categories_uuid),
        'name': display_name or _('商品'),
        'spec': (p.specification or '').strip(),
        'sale_price': disc_f if disc_f is not None else price_f,
        'original_price': price_f if disc_f is not None else None,
        'sales_label': _format_sales_count_label(sold_qty),
        'image_url': img,
        'catalog_url': url_for('catalog_category', category_id=p.product_categories_id),
    }


def build_home_new_arrivals():
    """自最近商品中挑有圖且圖可顯示者，再隨機抽若干筆給首頁「新貨上架」。"""
    rows = (
        ProductDetail.query.options(joinedload(ProductDetail.supplier))
        .filter(
            ProductDetail.image_path.isnot(None),
            ProductDetail.image_path != '',
        )
        .order_by(ProductDetail.create_time.desc())
        .limit(HOME_NEW_ARRIVALS_SCAN_LIMIT)
        .all()
    )
    with_displayable = [p for p in rows if _promo_image_will_display(p.image_path)]
    if not with_displayable:
        return []
    k = min(HOME_NEW_ARRIVALS_DISPLAY, len(with_displayable))
    picked = random.sample(with_displayable, k)
    return [_product_detail_to_promo_card(p) for p in picked]


def build_home_promo_deals():
    """有特價（特價低於原價）且圖可顯示的商品中，隨機抽若干筆給首頁「易賞價」。"""
    rows = (
        ProductDetail.query.options(joinedload(ProductDetail.supplier))
        .filter(
            ProductDetail.discount_price.isnot(None),
            ProductDetail.discount_price < ProductDetail.price,
            ProductDetail.image_path.isnot(None),
            ProductDetail.image_path != '',
        )
        .order_by(ProductDetail.create_time.desc())
        .limit(HOME_PROMO_DEALS_SCAN_LIMIT)
        .all()
    )
    with_displayable = [p for p in rows if _promo_image_will_display(p.image_path)]
    if not with_displayable:
        return []
    k = min(HOME_PROMO_DEALS_DISPLAY, len(with_displayable))
    picked = random.sample(with_displayable, k)
    return [_product_detail_to_promo_card(p) for p in picked]


def build_home_discount_shelf_products():
    rows = (
        ProductDetail.query.options(joinedload(ProductDetail.supplier))
        .filter(
            ProductDetail.discount_price.isnot(None),
            ProductDetail.discount_price < ProductDetail.price,
            ProductDetail.image_path.isnot(None),
            ProductDetail.image_path != '',
        )
        .order_by(ProductDetail.create_time.desc())
        .limit(HOME_PROMO_DEALS_SCAN_LIMIT)
        .all()
    )
    with_displayable = [p for p in rows if _promo_image_will_display(p.image_path)]
    if not with_displayable:
        return []
    k = min(HOME_DISCOUNT_SHELF_DISPLAY, len(with_displayable))
    picked = random.sample(with_displayable, k)
    cards = []
    for p in picked:
        cards.append(_product_detail_to_shelf_card(p))
    return cards


def _build_home_generic_shelf_pool():
    rows = (
        ProductDetail.query.options(joinedload(ProductDetail.supplier))
        .filter(
            ProductDetail.image_path.isnot(None),
            ProductDetail.image_path != '',
        )
        .order_by(ProductDetail.create_time.desc())
        .limit(HOME_GENERIC_SHELF_SCAN_LIMIT)
        .all()
    )
    with_displayable = [p for p in rows if _promo_image_will_display(p.image_path)]
    if not with_displayable:
        return []
    product_ids = [p.product_categories_uuid for p in with_displayable if p.product_categories_uuid is not None]

    sales_by_product = {}
    review_by_product = {}
    if product_ids:
        sales_rows = (
            db.session.query(
                OrderItem.product_details_uuid,
                func.sum(OrderItem.quantity).label('sold_qty'),
            )
            .join(Order, Order.order_uuid == OrderItem.order_uuid)
            .filter(
                Order.order_status == 'paid',
                OrderItem.product_details_uuid.in_(product_ids),
            )
            .group_by(OrderItem.product_details_uuid)
            .all()
        )
        sales_by_product = {
            row[0]: int(row[1] or 0)
            for row in sales_rows
            if row[0] is not None
        }
        review_rows = (
            db.session.query(
                Evaluate.product_details_uuid,
                func.count(Evaluate.evaluate_uuid).label('review_count'),
            )
            .filter(Evaluate.product_details_uuid.in_(product_ids))
            .group_by(Evaluate.product_details_uuid)
            .all()
        )
        review_by_product = {
            row[0]: int(row[1] or 0)
            for row in review_rows
            if row[0] is not None
        }

    cards = []
    for p in with_displayable:
        brand = (p.supplier.supplier_name if p.supplier is not None else '') or ''
        brand = brand.strip()
        pname = (p.product_name or '').strip()
        display_name = f'{brand} {pname}'.strip() if brand else pname
        discount_price = float(p.discount_price) if p.discount_price is not None else None
        price = float(p.price)
        sold_qty = sales_by_product.get(p.product_categories_uuid, 0)
        review_qty = review_by_product.get(p.product_categories_uuid, 0)
        cards.append(
            {
                'uuid': str(p.product_categories_uuid),
                'name': display_name or _('商品'),
                'spec': (p.specification or '').strip(),
                'sale': f'{(discount_price if discount_price is not None else price):.2f}',
                'orig': f'{price:.2f}' if discount_price is not None else '',
                'sales': _format_sales_count_label(sold_qty) if sold_qty > 0 else _('人氣商品'),
                'reviews': f'{review_qty}+' if review_qty > 0 else '0+',
                'image_url': product_image_url(p.image_path),
            }
        )
    return cards


def build_home_generic_shelf_groups():
    pool = _build_home_generic_shelf_pool()
    groups = {key: [] for key in HOME_GENERIC_SHELF_KEYS}
    if not pool:
        return groups

    group_size = min(HOME_DISCOUNT_SHELF_DISPLAY, len(pool))
    previous_group_ids = set()

    for key in HOME_GENERIC_SHELF_KEYS:
        candidate_pool = [
            card for card in pool
            if card.get('uuid') not in previous_group_ids
        ]
        if len(candidate_pool) < group_size:
            candidate_pool = list(pool)

        if group_size >= len(candidate_pool):
            group = random.sample(candidate_pool, len(candidate_pool))
        else:
            group = random.sample(candidate_pool, group_size)

        groups[key] = group
        previous_group_ids = {card.get('uuid') for card in group if card.get('uuid')}
    return groups


def build_home_case_deal_products():
    rows = (
        ProductDetail.query.options(joinedload(ProductDetail.supplier))
        .filter(
            ProductDetail.image_path.isnot(None),
            ProductDetail.image_path != '',
        )
        .order_by(ProductDetail.create_time.desc())
        .limit(HOME_CASE_DEAL_SCAN_LIMIT)
        .all()
    )
    candidates = [
        p for p in rows
        if _promo_image_will_display(p.image_path) and _is_case_deal_candidate(p)
    ]
    if not candidates:
        return []
    k = min(HOME_CASE_DEAL_DISPLAY, len(candidates))
    picked = random.sample(candidates, k)
    return [_product_detail_to_shelf_card(p) for p in picked]


def build_home_focus_recommendations():
    sales_rows = (
        db.session.query(
            OrderItem.product_details_uuid,
            func.sum(OrderItem.quantity).label('sold_qty'),
        )
        .join(Order, Order.order_uuid == OrderItem.order_uuid)
        .filter(Order.order_status == 'paid')
        .group_by(OrderItem.product_details_uuid)
        .order_by(func.sum(OrderItem.quantity).desc(), func.max(Order.create_time).desc())
        .limit(HOME_FOCUS_RECOMMENDATIONS_DISPLAY * 4)
        .all()
    )
    sold_by_product = {
        row[0]: int(row[1] or 0)
        for row in sales_rows
        if row[0] is not None
    }
    cards = []
    used_product_ids = set()

    if sold_by_product:
        product_rows = (
            ProductDetail.query.options(joinedload(ProductDetail.supplier))
            .filter(ProductDetail.product_categories_uuid.in_(list(sold_by_product.keys())))
            .all()
        )
        products_by_id = {row.product_categories_uuid: row for row in product_rows}

        for product_id, sold_qty in sold_by_product.items():
            product = products_by_id.get(product_id)
            if product is None or not _promo_image_will_display(product.image_path):
                continue
            cards.append(_product_detail_to_focus_card(product, sold_qty))
            used_product_ids.add(product_id)
            if len(cards) >= HOME_FOCUS_RECOMMENDATIONS_DISPLAY:
                return cards

    filler_rows = (
        ProductDetail.query.options(joinedload(ProductDetail.supplier))
        .filter(
            ProductDetail.image_path.isnot(None),
            ProductDetail.image_path != '',
        )
        .order_by(ProductDetail.create_time.desc())
        .limit(HOME_FOCUS_RECOMMENDATIONS_DISPLAY * 8)
        .all()
    )
    filler_candidates = [
        row for row in filler_rows
        if row.product_categories_uuid not in used_product_ids and _promo_image_will_display(row.image_path)
    ]
    if filler_candidates:
        remaining = HOME_FOCUS_RECOMMENDATIONS_DISPLAY - len(cards)
        picked = random.sample(filler_candidates, min(remaining, len(filler_candidates)))
        cards.extend(_product_detail_to_focus_card(product, 0) for product in picked)
    return cards


@app.context_processor
def inject_maternity_nav():
    out: dict = {'maternity_nav': None, 'food_nav': None}
    try:
        from app.maternity_nav import build_maternity_mega_nav

        out['maternity_nav'] = build_maternity_mega_nav()
    except Exception:
        app.logger.exception('母嬰導航載入失敗')
    try:
        from app.food_nav import build_food_mega_nav

        out['food_nav'] = build_food_mega_nav()
    except Exception:
        app.logger.exception('食品及飲品導航載入失敗')
    return out


@app.before_request
def before_request():
    g.locale = str(get_locale())


@app.route('/catalog/category/<int:category_id>', methods=['GET'])
def catalog_category(category_id):
    cat = db.session.get(ProductCategory, category_id)
    if cat is None:
        abort(404)

    supplier_id = request.args.get('supplier_id', type=int)
    supplier_row = db.session.get(Supplier, supplier_id) if supplier_id is not None else None
    if supplier_id is not None and supplier_row is None:
        abort(404)
    catalog_supplier_name = supplier_row.supplier_name if supplier_row is not None else None

    chain: list[ProductCategory] = []
    node: ProductCategory | None = cat
    while node is not None:
        chain.append(node)
        pid = node.parent_id
        node = db.session.get(ProductCategory, pid) if pid is not None else None
    chain.reverse()

    breadcrumbs = [{'label': _('首頁'), 'url': url_for('index')}]
    n = len(chain)
    for i, c in enumerate(chain):
        is_leaf_cat = i == n - 1
        if catalog_supplier_name and is_leaf_cat:
            leaf_url = url_for('catalog_category', category_id=c.product_categories_id)
        elif is_leaf_cat:
            leaf_url = None
        else:
            leaf_url = url_for('catalog_category', category_id=c.product_categories_id)
        breadcrumbs.append({'label': c.product_categories_name, 'url': leaf_url})
    if catalog_supplier_name:
        breadcrumbs.append({'label': catalog_supplier_name, 'url': None})

    all_cats = ProductCategory.query.order_by(ProductCategory.product_categories_id.asc()).all()
    children_by_parent: dict[int, list[ProductCategory]] = defaultdict(list)
    for c in all_cats:
        if c.parent_id is not None:
            children_by_parent[c.parent_id].append(c)
    for pid in children_by_parent:
        children_by_parent[pid].sort(key=lambda x: x.product_categories_id)

    rollup_ids = _collect_descendant_category_ids(category_id, children_by_parent)

    def _catalog_cat_url(cid: int) -> str:
        if supplier_id is not None:
            return url_for('catalog_category', category_id=cid, supplier_id=supplier_id)
        return url_for('catalog_category', category_id=cid)

    def _count_products_in_categories(cat_ids: list[int]) -> int:
        if not cat_ids:
            return 0
        cq = db.session.query(func.count(ProductDetail.product_categories_uuid)).filter(
            ProductDetail.product_categories_id.in_(cat_ids)
        )
        if supplier_id is not None:
            cq = cq.filter(ProductDetail.supplier_id == supplier_id)
        return int(cq.scalar() or 0)

    child_cats = (
        ProductCategory.query.filter_by(parent_id=category_id)
        .order_by(ProductCategory.product_categories_id.asc())
        .all()
    )

    subcategories = []
    if child_cats:
        strip_all_id = category_id
        all_rollup_ids = rollup_ids
        tiles = child_cats
    elif cat.parent_id is not None:
        strip_all_id = cat.parent_id
        tiles = list(children_by_parent.get(cat.parent_id, []))
        all_rollup_ids = _collect_descendant_category_ids(strip_all_id, children_by_parent)
    else:
        tiles = []

    if tiles:
        subcategories.append(
            {
                'label': _('全部'),
                'count': _count_products_in_categories(all_rollup_ids),
                'url': _catalog_cat_url(strip_all_id),
                'is_active': category_id == strip_all_id,
            }
        )
        for ch in tiles:
            sub_rollup = _collect_descendant_category_ids(ch.product_categories_id, children_by_parent)
            subcategories.append(
                {
                    'label': ch.product_categories_name,
                    'count': _count_products_in_categories(sub_rollup),
                    'url': _catalog_cat_url(ch.product_categories_id),
                    'is_active': ch.product_categories_id == category_id,
                }
            )

    brand_rows = (
        db.session.query(
            Supplier.supplier_id,
            Supplier.supplier_name,
            func.count(ProductDetail.product_categories_uuid),
        )
        .join(ProductDetail, ProductDetail.supplier_id == Supplier.supplier_id)
        .filter(ProductDetail.product_categories_id.in_(rollup_ids))
        .group_by(Supplier.supplier_id, Supplier.supplier_name)
        .order_by(func.count(ProductDetail.product_categories_uuid).desc())
        .limit(48)
        .all()
    )
    catalog_brands = []
    for r in brand_rows:
        sid, sname, cnt = r[0], r[1], int(r[2] or 0)
        catalog_brands.append(
            {
                'supplier_id': sid,
                'label': sname,
                'count': cnt,
                'url': url_for(
                    'catalog_category',
                    category_id=category_id,
                    supplier_id=sid,
                    view='brand',
                ),
                'is_active': supplier_id == sid,
            }
        )

    catalog_show_nav = bool(subcategories) or bool(catalog_brands)

    raw_view = (request.args.get('view') or '').strip().lower()
    if raw_view in ('category', 'brand'):
        catalog_view = raw_view
    elif not subcategories and catalog_brands:
        catalog_view = 'brand'
    else:
        catalog_view = 'category'

    def _catalog_tab_url(view: str) -> str:
        if supplier_id is not None:
            return url_for(
                'catalog_category',
                category_id=category_id,
                view=view,
                supplier_id=supplier_id,
            )
        return url_for('catalog_category', category_id=category_id, view=view)

    brand_nav_title = None
    if supplier_id is not None and catalog_supplier_name:
        brand_nav_title = _('目前篩選：%(brand)s（可在此切換其他品牌）') % {'brand': catalog_supplier_name}

    catalog_nav_tabs = [
        {
            'key': 'category',
            'label': _('分類'),
            'url': _catalog_tab_url('category'),
            'active': catalog_view == 'category',
            'disabled': False,
        },
        {
            'key': 'brand',
            'label': _('品牌'),
            'url': _catalog_tab_url('brand'),
            'active': catalog_view == 'brand',
            'disabled': False,
            'link_title': brand_nav_title,
        },
    ]

    q = ProductDetail.query.options(joinedload(ProductDetail.supplier)).filter(
        ProductDetail.product_categories_id.in_(rollup_ids)
    )
    if supplier_id is not None:
        q = q.filter(ProductDetail.supplier_id == supplier_id)
    rows = q.order_by(ProductDetail.product_name.asc()).limit(120).all()

    products = []
    for i, p in enumerate(rows):
        img = product_image_url(p.image_path)
        brand = (p.supplier.supplier_name if p.supplier is not None else '') or ''
        brand = brand.strip()
        product_name = (p.product_name or '').strip()
        display_name = f'{brand} {product_name}'.strip() if brand else product_name
        products.append(
            {
                'uuid': str(p.product_categories_uuid),
                'name': display_name,
                'unit': p.specification or '',
                'price': float(p.price),
                'discount_price': float(p.discount_price) if p.discount_price is not None else None,
                'img_mod': (i % 8) + 1,
                'image_url': img,
            }
        )

    if catalog_supplier_name:
        title = f'{cat.product_categories_name} · {catalog_supplier_name} - PNS'
    else:
        title = f'{cat.product_categories_name} - PNS'

    return render_template(
        'category_browse.html.j2',
        title=title,
        browse_title=cat.product_categories_name,
        catalog_supplier_name=catalog_supplier_name,
        breadcrumbs=breadcrumbs,
        products=products,
        subcategories=subcategories,
        filter_tabs=[],
        sort_options=[],
        browse_source='catalog',
        supplier_id=supplier_id,
        category_id=category_id,
        catalog_view=catalog_view,
        catalog_nav_tabs=catalog_nav_tabs,
        catalog_brands=catalog_brands,
        catalog_show_nav=catalog_show_nav,
    )


@app.route('/browse/<section>/<slug>', methods=['GET'])
def category_browse(section, slug):
    ctx = build_browse_page(section, slug)
    if ctx is None:
        abort(404)
    return render_template('category_browse.html.j2', **ctx)


@app.route('/cart', methods=['GET'])
def cart():
    cart_items = []
    total_price = 0.0
    
    if current_user.is_authenticated:
        # Authenticated user: get from database
        cart_rows = (
            Cart.query.filter_by(user_uuid=current_user.user_uuid)
            .join(ProductDetail, ProductDetail.product_categories_uuid == Cart.product_details_uuid)
            .all()
        )
        for row in cart_rows:
            product = row.product
            if product is None:
                continue
            price = float(product.discount_price if product.discount_price is not None else product.price)
            cart_items.append(
                {
                    'product_uuid': str(product.product_categories_uuid),
                    'name': product.product_name,
                    'image_url': product_image_url(product.image_path),
                    'unit_price': price,
                    'line_total': price,
                }
            )
            total_price += price
    else:
        # Anonymous user: get from session
        cart_data = session.get('cart', {})
        for product_uuid, quantity in cart_data.items():
            try:
                product_id = uuid.UUID(product_uuid)
                product = db.session.get(ProductDetail, product_id)
                if product is None:
                    continue
                price = float(product.discount_price if product.discount_price is not None else product.price)
                cart_items.append(
                    {
                        'product_uuid': product_uuid,
                        'name': product.product_name,
                        'image_url': product_image_url(product.image_path),
                        'unit_price': price,
                        'line_total': price * quantity,
                        'quantity': quantity,
                    }
                )
                total_price += price * quantity
            except ValueError:
                continue
    
    return render_template('cart.html.j2', cart_items=cart_items, total_price=total_price)


@app.route('/cart/add', methods=['POST'])
def add_cart():
    data = request.get_json(silent=True) or request.form
    product_uuid = (data.get('product_uuid') or data.get('product_uuid') or '').strip()
    if not product_uuid:
        return jsonify({'status': 'error', 'message': '缺少 product_uuid'}), 400
    try:
        product_id = uuid.UUID(product_uuid)
    except ValueError:
        return jsonify({'status': 'error', 'message': '無效的商品識別'}), 400
    product = db.session.get(ProductDetail, product_id)
    if product is None:
        return jsonify({'status': 'error', 'message': '找不到商品'}), 404
    
    if current_user.is_authenticated:
        # Authenticated user: add to database
        existing = db.session.get(Cart, (current_user.user_uuid, product.product_categories_uuid))
        if existing is None:
            db.session.add(Cart(user_uuid=current_user.user_uuid, product_details_uuid=product.product_categories_uuid))
            db.session.commit()
        cart_count = Cart.query.filter_by(user_uuid=current_user.user_uuid).count()
    else:
        # Anonymous user: add to session
        cart = session.get('cart', {})
        cart[product_uuid] = cart.get(product_uuid, 0) + 1
        session['cart'] = cart
        cart_count = sum(cart.values())
    
    return jsonify({'status': 'ok', 'cart_count': cart_count})


@app.route('/cart/remove', methods=['POST'])
def cart_remove():
    data = request.get_json(silent=True) or request.form
    product_uuid = (data.get('product_uuid') or '').strip()
    if not product_uuid:
        return jsonify({'status': 'error', 'message': '缺少 product_uuid'}), 400
    try:
        product_id = uuid.UUID(product_uuid)
    except ValueError:
        return jsonify({'status': 'error', 'message': '無效的商品識別'}), 400
    
    if current_user.is_authenticated:
        # Authenticated user: remove from database
        row = db.session.get(Cart, (current_user.user_uuid, product_id))
        if row:
            db.session.delete(row)
            db.session.commit()
        cart_count = Cart.query.filter_by(user_uuid=current_user.user_uuid).count()
    else:
        # Anonymous user: remove from session
        cart = session.get('cart', {})
        if product_uuid in cart:
            del cart[product_uuid]
            session['cart'] = cart
        cart_count = sum(cart.values())
    
    if request.is_json:
        return jsonify({'status': 'ok', 'cart_count': cart_count})
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_rows = (
        Cart.query.filter_by(user_uuid=current_user.user_uuid)
        .join(ProductDetail, ProductDetail.product_categories_uuid == Cart.product_details_uuid)
        .all()
    )
    if not cart_rows:
        flash('您的購物車目前沒有商品。')
        return redirect(url_for('cart'))
    address_rows = current_user.addresses.order_by(UserAddress.create_time.asc()).all()
    selected_address = next((addr for addr in address_rows if addr.is_default), None) or (address_rows[0] if address_rows else None)
    receiver_name = current_user.username
    receiver_phone = (current_user.phone_number or '').strip() or ((selected_address.phone_number or '').strip() if selected_address else '')
    receiver_address = selected_address.formatted_line() if selected_address else '尚未設定送貨地址'
    has_valid_address = bool(selected_address and receiver_address.strip())
    delivery_address_url = url_for('delivery_address', next=url_for('checkout'), open='1')
    selected_delivery_slot = (request.form.get('delivery_slot') or 'morning').strip()
    delivery_slot_choices = _delivery_slot_choices()
    total_price = 0.0
    items = []
    for row in cart_rows:
        product = row.product
        if product is None:
            continue
        price = float(product.discount_price if product.discount_price is not None else product.price)
        items.append(
            {
                'product_uuid': str(product.product_categories_uuid),
                'name': product.product_name,
                'image_url': product_image_url(product.image_path),
                'unit_price': price,
                'quantity': 1,
                'line_total': price,
            }
        )
        total_price += price
    if request.method == 'POST':
        if not receiver_phone or not has_valid_address:
            flash('請先填寫送貨地址與聯絡電話。')
            return redirect(delivery_address_url)
        if not _delivery_slot_label(selected_delivery_slot):
            flash('請先選擇配送時間。')
            return render_template(
                'checkout.html.j2',
                items=items,
                total_price=total_price,
                receiver_name=receiver_name,
                receiver_phone=receiver_phone,
                receiver_address=receiver_address,
                has_valid_address=has_valid_address,
                delivery_address_url=delivery_address_url,
                delivery_slot_choices=delivery_slot_choices,
                selected_delivery_slot=selected_delivery_slot,
            )
        order = Order(
            user_uuid=current_user.user_uuid,
            order_status='paid',
            receiver_name=receiver_name,
            receiver_phone=receiver_phone,
            receiver_address_snapshot=receiver_address,
            total_price=total_price,
        )
        db.session.add(order)
        db.session.flush()
        for item in items:
            order_item = OrderItem(
                order_uuid=order.order_uuid,
                product_details_uuid=uuid.UUID(item['product_uuid']),
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                line_total=item['line_total'],
            )
            db.session.add(order_item)
        feature_tables = _order_feature_tables_state()
        if feature_tables['delivery']:
            db.session.add(
                Delivery(
                    user_uuid=current_user.user_uuid,
                    order_uuid=order.order_uuid,
                    deliver_time=_build_delivery_time(selected_delivery_slot),
                )
            )
        if feature_tables['payment_log']:
            db.session.add(
                PaymentLog(
                    user_uuid=current_user.user_uuid,
                    order_uuid=order.order_uuid,
                    payment_methods='網上付款',
                    price=total_price,
                    state='paid',
                )
            )
        membership = _get_or_create_membership(current_user)
        earned_points = _calculate_earned_points(total_price)
        if earned_points > 0:
            db.session.add(
                MembershipPointsLog(
                    user_uuid=current_user.user_uuid,
                    transaction_time=_build_points_log_timestamp(order.create_time),
                    retailer=POINTS_LOG_RETAILER,
                    store_name=_points_order_store_name(order),
                    transaction_amount_hkd=total_price,
                    base_points=earned_points,
                    extra_points=0,
                    redeemed_points=None,
                )
            )
            membership.membership_point = int(membership.membership_point or 0) + earned_points
        Cart.query.filter_by(user_uuid=current_user.user_uuid).delete(synchronize_session=False)
        db.session.commit()
        return render_template(
            'order_confirmation.html.j2',
            order=order,
            items=items,
            delivery_time_label=_delivery_slot_label(selected_delivery_slot),
        )
    return render_template(
        'checkout.html.j2',
        items=items,
        total_price=total_price,
        receiver_name=receiver_name,
        receiver_phone=receiver_phone,
        receiver_address=receiver_address,
        has_valid_address=has_valid_address,
        delivery_address_url=delivery_address_url,
        delivery_slot_choices=delivery_slot_choices,
        selected_delivery_slot=selected_delivery_slot,
    )


@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    home_new_arrivals = build_home_new_arrivals()
    home_promo_deals = build_home_promo_deals()
    home_discount_shelf_products = build_home_discount_shelf_products()
    home_generic_shelf_groups = build_home_generic_shelf_groups()
    home_case_deal_products = build_home_case_deal_products()
    home_focus_recommendations = build_home_focus_recommendations()
    newest_cid = (
        db.session.query(ProductDetail.product_categories_id)
        .order_by(ProductDetail.create_time.desc())
        .limit(1)
        .scalar()
    )
    home_new_view_all_url = (
        url_for('catalog_category', category_id=newest_cid) if newest_cid is not None else url_for('index')
    )
    deals_view_cid = (
        db.session.query(ProductDetail.product_categories_id)
        .filter(
            ProductDetail.discount_price.isnot(None),
            ProductDetail.discount_price < ProductDetail.price,
        )
        .order_by(ProductDetail.create_time.desc())
        .limit(1)
        .scalar()
    )
    home_promo_deals_view_all_url = (
        url_for('catalog_category', category_id=deals_view_cid)
        if deals_view_cid is not None
        else home_new_view_all_url
    )
    ctx = {
        'home_new_arrivals': home_new_arrivals,
        'home_new_view_all_url': home_new_view_all_url,
        'home_promo_deals': home_promo_deals,
        'home_promo_deals_view_all_url': home_promo_deals_view_all_url,
        'home_discount_shelf_products': home_discount_shelf_products,
        'home_generic_shelf_groups': home_generic_shelf_groups,
        'home_case_deal_products': home_case_deal_products,
        'home_focus_recommendations': home_focus_recommendations,
    }
    if current_user.is_anonymous:
        return render_template('index.html.j2', title=_('PNS 網購'), **ctx)
    return render_template('index.html.j2', title=_('Home'), **ctx)


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
        session.permanent = True
        login_user(user, remember=form.remember_me.data)
        # Migrate cart from session to database
        cart = session.get('cart', {})
        if cart:
            for product_uuid, quantity in cart.items():
                try:
                    product_id = uuid.UUID(product_uuid)
                    # Check if already in database cart
                    existing = db.session.get(Cart, (user.user_uuid, product_id))
                    if existing is None:
                        for _ in range(quantity):
                            db.session.add(Cart(user_uuid=user.user_uuid, product_details_uuid=product_id))
                except ValueError:
                    continue
            db.session.commit()
            session.pop('cart', None)  # Clear session cart
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

        pending_rows = _ip_window_pending_registration_rows(ip)
        existing = next(
            (
                row for row in pending_rows
                if (row.mail or '').strip().lower() == pending_mail.lower()
            ),
            None,
        )
        if existing is None and len(pending_rows) >= REG_VERIFY_IP_MAX_PENDING:
            flash(
                f'此 IP 15 分鐘內最多只可註冊 {REG_VERIFY_IP_MAX_PENDING} 個郵箱，請稍後再試。'
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
    membership = None
    points_summary = None
    dashboard_stamps = []
    recent_purchase_items = []

    if current_user.is_authenticated and profile_user == current_user:
        membership, _, points_summary = _sync_membership_points(profile_user, commit=True)
        dashboard_stamps = _build_dashboard_stamps()
        recent_purchase_items = _build_recent_purchase_items(profile_user)

    return render_template(
        'user.html.j2',
        user=profile_user,
        membership=membership,
        points_summary=points_summary,
        dashboard_stamps=dashboard_stamps,
        recent_purchase_items=recent_purchase_items,
    )


@app.route('/order_history', methods=['GET'])
@login_required
def order_history():
    orders = current_user.orders.order_by(Order.create_time.desc()).all()
    order_cards = []
    feature_tables = _order_feature_tables_state()

    for order in orders:
        items = []
        item_count = 0
        refund_form = OrderRefundForm(prefix=f'refund-{order.order_uuid}')
        refunded = (
            (feature_tables['refund'] and order.refunds.count() > 0)
            or (order.order_status or '').strip().lower() in ('refund', 'refunded', '退款')
        )
        delivery_time_label = ''
        if feature_tables['delivery']:
            delivery_row = order.deliveries.order_by(Delivery.create_time.asc()).first()
            if delivery_row is not None:
                delivery_time_label = _delivery_time_label(delivery_row.deliver_time)

        for item in order.items.order_by(OrderItem.create_time.asc()).all():
            qty = int(item.quantity or 0)
            item_count += qty
            product = item.product
            existing_review = None
            review_form = None
            review_enabled = feature_tables['evaluate'] and not refunded
            review_disabled_text = ''
            if feature_tables['evaluate']:
                existing_review = Evaluate.query.filter_by(
                    user_uuid=current_user.user_uuid,
                    product_details_uuid=item.product_details_uuid,
                ).first()
                review_form = ProductReviewForm(prefix=f'review-{item.order_item_uuid}')
                if existing_review is not None:
                    review_form.review_text.data = existing_review.evalate_txt or ''
                if refunded:
                    review_disabled_text = _('訂單已退款，評論已取消')
            else:
                review_disabled_text = _('評論功能尚未初始化')
            items.append(
                {
                    'order_item_uuid': str(item.order_item_uuid),
                    'product_uuid': str(item.product_details_uuid),
                    'name': ((product.product_name if product else '') or _('商品')).strip(),
                    'image_url': product_image_url(product.image_path) if product and product.image_path else '',
                    'quantity': qty,
                    'unit_price': float(item.unit_price or 0),
                    'line_total': float(item.line_total or 0),
                    'review_form': review_form,
                    'review_enabled': review_enabled,
                    'review_disabled_text': review_disabled_text,
                    'review_text': '' if refunded else ((existing_review.evalate_txt or '').strip() if existing_review else ''),
                }
            )

        order_cards.append(
            {
                'order': order,
                'order_code': str(order.order_uuid).split('-')[0].upper(),
                'item_count': item_count,
                'line_items': items,
                'status_label': _display_order_status(order.order_status),
                'delivery_time_label': delivery_time_label,
                'refund_enabled': feature_tables['refund'],
                'can_refund': feature_tables['refund'] and not refunded,
                'refund_form': refund_form,
            }
        )

    return render_template(
        'partials/info-page_orders.html.j2',
        title='訂單紀錄',
        order_cards=order_cards,
    )


@app.route('/order_history/refund/<order_uuid>', methods=['POST'])
@login_required
def order_refund(order_uuid):
    feature_tables = _order_feature_tables_state()
    if not feature_tables['refund']:
        flash('退款功能尚未初始化，請先執行資料庫升級。')
        return redirect(url_for('order_history'))

    form = OrderRefundForm(prefix=f'refund-{order_uuid}')
    if not form.validate_on_submit():
        flash('退款操作無效，請再試一次。')
        return redirect(url_for('order_history'))

    try:
        order_id = uuid.UUID(str(order_uuid))
    except ValueError:
        abort(404)

    order = current_user.orders.filter(Order.order_uuid == order_id).first_or_404()
    already_refunded = order.refunds.count() > 0 or (order.order_status or '').strip().lower() in ('refund', 'refunded', '退款')
    if already_refunded:
        flash('此訂單已退款。')
        return redirect(url_for('order_history'))

    db.session.add(Refund(order_uuid=order.order_uuid, user_uuid=current_user.user_uuid))
    order.order_status = '退款'

    if feature_tables['payment_log']:
        payment_logs = order.payment_logs.order_by(PaymentLog.create_time.asc()).all()
        if payment_logs:
            for log in payment_logs:
                log.state = 'refunded'
        else:
            db.session.add(
                PaymentLog(
                    user_uuid=current_user.user_uuid,
                    order_uuid=order.order_uuid,
                    payment_methods='退款',
                    price=order.total_price,
                    state='refunded',
                )
            )

    if feature_tables['evaluate']:
        reviewed_product_ids = [
            item.product_details_uuid
            for item in order.items.order_by(OrderItem.create_time.asc()).all()
            if item.product_details_uuid is not None
        ]
        if reviewed_product_ids:
            reviews = (
                Evaluate.query.filter(
                    Evaluate.user_uuid == current_user.user_uuid,
                    Evaluate.product_details_uuid.in_(reviewed_product_ids),
                ).all()
            )
            for review in reviews:
                db.session.delete(review)

    membership = _get_or_create_membership(current_user)
    earned_points = _calculate_earned_points(order.total_price)
    if earned_points > 0:
        refund_store_name = _points_refund_store_name(order)
        refund_log = current_user.points_logs.filter_by(
            retailer=POINTS_LOG_RETAILER,
            store_name=refund_store_name,
        ).first()
        if refund_log is None:
            db.session.add(
                MembershipPointsLog(
                    user_uuid=current_user.user_uuid,
                    transaction_time=datetime.utcnow(),
                    retailer=POINTS_LOG_RETAILER,
                    store_name=refund_store_name,
                    transaction_amount_hkd=order.total_price or 0,
                    base_points=0,
                    extra_points=0,
                    redeemed_points=earned_points,
                )
            )
        membership.membership_point = max(int(membership.membership_point or 0) - earned_points, 0)

    db.session.commit()
    flash('已提交退款申請。')
    return redirect(url_for('order_history'))


@app.route('/order_history/review/<product_uuid>/<order_item_uuid>', methods=['POST'])
@login_required
def order_review(product_uuid, order_item_uuid):
    feature_tables = _order_feature_tables_state()
    if not feature_tables['evaluate']:
        flash('評論功能尚未初始化，請先執行資料庫升級。')
        return redirect(url_for('order_history'))

    form = ProductReviewForm(prefix=f'review-{order_item_uuid}')
    if not form.validate_on_submit():
        if form.review_text.errors:
            flash(form.review_text.errors[0])
        else:
            flash('評論提交失敗，請再試一次。')
        return redirect(url_for('order_history'))

    try:
        product_id = uuid.UUID(str(product_uuid))
        order_item_id = uuid.UUID(str(order_item_uuid))
    except ValueError:
        abort(404)

    order_item = (
        OrderItem.query.join(Order, Order.order_uuid == OrderItem.order_uuid)
        .filter(
            OrderItem.order_item_uuid == order_item_id,
            OrderItem.product_details_uuid == product_id,
            Order.user_uuid == current_user.user_uuid,
        )
        .first_or_404()
    )
    if _is_refunded_order(order_item.order):
        flash('已退款訂單不能評論商品。')
        return redirect(url_for('order_history'))

    content = (form.review_text.data or '').strip()
    review = Evaluate.query.filter_by(
        user_uuid=current_user.user_uuid,
        product_details_uuid=order_item.product_details_uuid,
    ).first()

    if review is None:
        review = Evaluate(
            product_details_uuid=order_item.product_details_uuid,
            user_uuid=current_user.user_uuid,
            evalate_txt=content,
        )
        db.session.add(review)
    else:
        review.evalate_txt = content

    db.session.commit()
    flash('商品評論已儲存。')
    return redirect(url_for('order_history'))


@app.route('/product_reviews', methods=['GET'])
@login_required
def product_reviews():
    _cleanup_refunded_reviews(current_user, commit=True)
    review_summary = _build_product_review_cards(current_user)
    return render_template(
        'partials/info-page_product-reviews.html.j2',
        title='產品評價',
        review_cards=review_summary['cards'],
        reviewed_count=review_summary['count'],
        latest_review_at=review_summary['latest_review_at'],
    )


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
    delivery_next_url = _safe_internal_redirect_target(request.args.get('next'), 'delivery_address')
    auto_open_modal = (request.args.get('open') or '').strip() == '1'
    return render_template(
        'partials/info-page_delivery-address.html.j2',
        title='送貨地址',
        addresses=addresses,
        form=form,
        hk_districts=HK_DISTRICTS,
        delivery_next_url=delivery_next_url,
        auto_open_modal=auto_open_modal,
    )


@app.route('/membership_points', methods=['GET'])
@login_required
def membership_points():
    membership, logs, points_summary = _sync_membership_points(current_user, commit=True)

    return render_template(
        'partials/info-page_membership-points.html.j2',
        title='易賞錢積分',
        membership=membership,
        points_logs=logs,
        hkd_equivalent=points_summary['hkd_equivalent'],
        expiring_points=points_summary['expiring_points'],
        expiry_date=points_summary['expiry_date'],
        points_summary=points_summary,
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
    next_url = _safe_internal_redirect_target(request.args.get('next'), 'delivery_address')
    retry_url = url_for('delivery_address', next=next_url, open='1')
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
        return redirect(next_url)

    flash('請檢查輸入資料。')
    return redirect(retry_url)


@app.route('/delivery_address/set_default/<user_address_uuid>', methods=['GET'])
@login_required
def delivery_address_set_default(user_address_uuid):
    next_url = _safe_internal_redirect_target(request.args.get('next'), 'delivery_address')
    # 僅允許設定為自己的地址
    addresses = current_user.addresses.all()
    target = None
    for a in addresses:
        if str(a.user_address_uuid) == str(user_address_uuid):
            target = a
            break
    if target is None:
        return redirect(next_url)

    for a in addresses:
        a.is_default = False
    target.is_default = True
    db.session.commit()
    flash('已設定預設送貨地址。')
    return redirect(next_url)


@app.route('/delivery_address/delete/<user_address_uuid>', methods=['GET'])
@login_required
def delivery_address_delete(user_address_uuid):
    next_url = _safe_internal_redirect_target(request.args.get('next'), 'delivery_address')
    addresses = current_user.addresses.order_by(UserAddress.create_time.desc()).all()
    target = None
    for a in addresses:
        if str(a.user_address_uuid) == str(user_address_uuid):
            target = a
            break
    if target is None:
        return redirect(next_url)

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
    return redirect(next_url)
