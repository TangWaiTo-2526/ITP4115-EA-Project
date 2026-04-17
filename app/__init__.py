import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
import os
from flask import Flask, request
from app.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel


app = Flask(__name__, static_folder='.', static_url_path='/app')
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager()
login.login_view = "login"
login.init_app(app)
mail = Mail(app)
bootstrap = Bootstrap(app)
moment = Moment(app)


def get_locale():
    # 依瀏覽器語言偏好順序逐一判斷；不要因為後面出現中文就覆蓋前面的英文偏好
    accepted = [lang.lower() for lang, _q in request.accept_languages]
    for lang in accepted:
        if lang.startswith('en'):
            return 'en'
        if lang.startswith('es'):
            return 'es'
        if lang.startswith('zh'):
            # 簡中：zh-CN / zh-SG / zh-Hans
            if ('hans' in lang) or lang.startswith('zh-cn') or lang.startswith('zh-sg'):
                return 'zh_Hans'
            # 其餘中文（zh / zh-TW / zh-HK / zh-MO / zh-Hant）統一走繁中 catalog（zh）
            return 'zh'

    # 其餘語言：依支援語系直接回傳；不支援時才預設繁中
    match = request.accept_languages.best_match(app.config['LANGUAGES']) or 'zh'
    if match in ('en', 'es', 'zh', 'zh_Hans'):
        return match
    return 'zh'


babel = Babel(app, locale_selector=get_locale)

if not app.debug:
    root = logging.getLogger()
    if app.config["MAIL_SERVER"]:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'], subject='Microblog Failure',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        root.addHandler(mail_handler)

    _log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(_log_dir, exist_ok=True)
    file_handler = RotatingFileHandler(
        os.path.join(_log_dir, 'microblog.log'), maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.setLevel(logging.INFO)
    root.info('Microblog startup')

from app import routes, errors