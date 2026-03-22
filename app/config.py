import os

basedir = os.path.abspath(os.path.dirname(__file__))
_root = os.path.abspath(os.path.join(basedir, '..'))

try:
    from dotenv import load_dotenv
    # override=False：終端已 export 的變數不會被 .env 覆蓋
    load_dotenv(os.path.join(_root, '.env'), override=False)
except ImportError:
    pass


def _env_password(name):
    """讀取密碼；空字串視為未設定（避免 .env 裡 MAIL_PASSWORD= 留空）"""
    v = os.environ.get(name)
    if v is None:
        return None
    v = v.strip()
    return v if v else None


def _env_bool(name, default):
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ('1', 'true', 'yes', 'on')


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI") or \
        'postgresql://postgres:postgres@localhost:5432/postgres'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'mail.spacemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '465'))
    MAIL_USE_TLS = _env_bool('MAIL_USE_TLS', False)
    MAIL_USE_SSL = _env_bool('MAIL_USE_SSL', True)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'pns@vtcit.top')
    MAIL_PASSWORD = _env_password('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'pns@vtcit.top')
    ADMINS = [MAIL_DEFAULT_SENDER]
    LANGUAGES = ['en', 'es', 'zh']
