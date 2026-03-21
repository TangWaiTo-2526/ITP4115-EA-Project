from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, \
    Length
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
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('此使用者名稱已被使用，請換一個。')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('此電子郵件已被註冊，請換一個。')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Request Password Reset'))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(),
                                           EqualTo('password')])
    submit = SubmitField(_l('Request Password Reset'))


class EditProfileForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About me'),
                             validators=[Length(min=0, max=140)])
    submit = SubmitField(_l('Submit'))

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError(_('Please use a different username.'))


class PostForm(FlaskForm):
    post = TextAreaField(_l('Say something'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))
