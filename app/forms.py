from sqlalchemy import func
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    TextAreaField,
    DateField,
    SelectField,
)
from wtforms.validators import (
    ValidationError,
    DataRequired,
    Email,
    EqualTo,
    Length,
    Regexp,
    Optional,
)
from app.models import User
from app.hk_address import HK_DISTRICTS, HK_REGIONS


class LoginForm(FlaskForm):
    username = StringField(
        '使用者名稱',
        validators=[DataRequired(message='請填寫使用者名稱')],
    )
    password = PasswordField(
        '密碼',
        validators=[DataRequired(message='請填寫密碼')],
    )
    remember_me = BooleanField('記住我')
    submit = SubmitField('登入')


class RegistrationForm(FlaskForm):
    username = StringField(
        '使用者名稱',
        validators=[DataRequired(message='請填寫使用者名稱')],
    )
    email = StringField(
        '電子郵件',
        validators=[
            DataRequired(message='請填寫電子郵件'),
            Email(message='請輸入有效的電子郵件地址'),
        ],
    )
    password = PasswordField(
        '密碼',
        validators=[DataRequired(message='請填寫密碼')],
    )
    password2 = PasswordField(
        '確認密碼',
        validators=[
            DataRequired(message='請再次輸入密碼'),
            EqualTo('password', message='兩次輸入的密碼必須相同'),
        ],
    )
    submit = SubmitField('註冊')

    def validate_username(self, username):
        user = User.query.filter_by(user_name=username.data).first()
        if user is not None:
            raise ValidationError('此使用者名稱已被使用，請換一個。')

    def validate_email(self, email):
        user = User.query.filter_by(mail=email.data).first()
        if user is not None:
            raise ValidationError('此電子郵件已被註冊，請換一個。')


class EmailVerificationForm(FlaskForm):
    code = StringField(
        '驗證碼',
        validators=[
            DataRequired(message='請輸入驗證碼'),
            Length(min=6, max=6, message='驗證碼為 6 位數字'),
            Regexp(r'^\d{6}$', message='請輸入 6 位數字'),
        ],
        render_kw={
            'maxlength': 6,
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
            'pattern': '[0-9]{6}',
        },
    )
    submit = SubmitField('確認並繼續')


class RegisterExtraForm(FlaskForm):
    """註冊第三步：電話必填，地址選填。"""

    phone = StringField(
        '電話號碼',
        validators=[
            DataRequired(message='請填寫電話號碼'),
            Regexp(r'^\d{8}$', message='請輸入 8 位數字香港電話號碼'),
        ],
        render_kw={
            'type': 'tel',
            'maxlength': 8,
            'inputmode': 'numeric',
            'pattern': r'[0-9]*',
            'autocomplete': 'tel',
            'title': '僅限 8 位數字',
        },
    )
    address = TextAreaField(
        '地址',
        validators=[Optional(), Length(max=1024, message='地址不能超過 1024 字')],
        render_kw={
            'rows': 3,
            'placeholder': '選填：收貨或聯絡地址',
        },
    )
    submit = SubmitField('完成註冊')


class ResendVerifyForm(FlaskForm):
    submit = SubmitField('重新發送驗證碼')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField(
        '電子郵件',
        validators=[
            DataRequired(message='請填寫電子郵件'),
            Email(message='請輸入有效的電子郵件地址'),
        ],
    )
    submit = SubmitField('寄送重設連結')


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        '新密碼',
        validators=[DataRequired(message='請填寫密碼')],
    )
    password2 = PasswordField(
        '確認新密碼',
        validators=[
            DataRequired(message='請再次輸入密碼'),
            EqualTo('password', message='兩次輸入的密碼必須相同'),
        ],
    )
    submit = SubmitField('重設密碼')


class EditProfileForm(FlaskForm):
    """帳戶中心「個人資料」：欄位對應 user 與 user_address 表。"""

    salutation = SelectField(
        '稱謂',
        choices=[
            ('', '請選擇'),
            ('先生', '先生'),
            ('女士', '女士'),
            ('博士', '博士'),
        ],
        validators=[Optional()],
    )
    username = StringField('姓名', validators=[DataRequired(message='請填寫姓名')])
    birthday = DateField('生日', validators=[Optional()], format='%Y-%m-%d')
    nationality = StringField('國籍', validators=[Optional(), Length(max=64)])
    mobile_phone = StringField(
        '手提電話號碼',
        validators=[
            Optional(),
            Regexp(r'^\d{8}$', message='請輸入 8 位數字香港手提電話號碼'),
        ],
        render_kw={'maxlength': 8, 'inputmode': 'numeric', 'autocomplete': 'tel'},
    )
    home_phone = StringField(
        '住宅電話號碼',
        validators=[Optional(), Length(max=32)],
        description='送貨地址聯絡用（存於收貨地址）',
    )
    mail = StringField(
        '電郵',
        validators=[
            DataRequired(message='請填寫電郵'),
            Email(message='請輸入有效的電郵地址'),
        ],
    )
    comm_language = SelectField(
        '通訊語言',
        choices=[('繁體', '繁體'), ('English', 'English')],
        validators=[Optional()],
    )
    addr_unit = StringField(
        '單位',
        validators=[Optional(), Length(max=64)],
        render_kw={'placeholder': '例如：03號／A室'},
    )
    addr_floor = StringField(
        '樓層',
        validators=[Optional(), Length(max=32)],
        render_kw={'placeholder': '例如：9樓'},
    )
    addr_building_street = StringField(
        '大廈、屋苑或街道',
        validators=[Optional(), Length(max=512)],
    )
    addr_region = SelectField(
        '區域',
        choices=[('', '請選擇')] + [(r, r) for r in HK_REGIONS],
        validators=[Optional()],
    )
    addr_district = SelectField('地區', choices=[('', '請選擇')], validators=[Optional()])
    marketing_opt_out = BooleanField(
        '我不希望接受有關最新的優惠、促銷、折扣或任何類似的訊息。',
    )
    brand_fortress = BooleanField('豐澤', default=True)
    brand_parknshop = BooleanField('百佳', default=True)
    brand_watsons = BooleanField('屈臣氏', default=True)
    brand_moneyback = BooleanField('易賞錢合作伙伴', default=True)
    submit = SubmitField('儲存', render_kw={'class': 'account-profile-submit-1'})

    def __init__(self, original_username, original_mail, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_mail = (original_mail or '').strip().lower()
        reg = (self.addr_region.data or '').strip()
        if reg in HK_DISTRICTS:
            self.addr_district.choices = [('', '請選擇')] + [(d, d) for d in HK_DISTRICTS[reg]]
        else:
            self.addr_district.choices = [('', '請選擇')]

    def validate_username(self, username):
        new_name = (username.data or '').strip()
        if new_name != (self.original_username or '').strip():
            user = User.query.filter_by(user_name=new_name).first()
            if user is not None:
                raise ValidationError('此姓名／使用者名稱已被使用，請換一個。')

    def validate_mail(self, mail):
        candidate = (mail.data or '').strip().lower()
        if candidate != self.original_mail:
            user = User.query.filter(func.lower(User.mail) == candidate).first()
            if user is not None:
                raise ValidationError('此電郵已被註冊，請換一個。')

    def validate_addr_district(self, field):
        r = (self.addr_region.data or '').strip()
        d = (field.data or '').strip()
        if d and r and d not in HK_DISTRICTS.get(r, ()):
            raise ValidationError('請選擇與區域相符的地區。')
