from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import (
    ValidationError,
    DataRequired,
    Email,
    EqualTo,
    Length,
    Regexp,
    Optional,
)
from flask_babel import _, lazy_gettext as _l
from app.models import User


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
    username = StringField(_l('Username'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(user_name=self.username.data).first()
            if user is not None:
                raise ValidationError(_('Please use a different username.'))
