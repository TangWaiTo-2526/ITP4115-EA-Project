
from datetime import datetime, timedelta, timezone
from hashlib import md5
import uuid

from app import app, db, login
import jwt
import sqlalchemy as sa

from flask_login import UserMixin
from sqlalchemy.dialects import postgresql

from werkzeug.security import generate_password_hash, check_password_hash


# ---------------------------------------------------------------------------
# 用戶（表名 user）：商城 / 登入註冊
# ---------------------------------------------------------------------------


class User(UserMixin, db.Model):
    """PostgreSQL 表名 user（與 SQL 關鍵字無衝突時使用 user 表）"""

    __tablename__ = 'user'

    user_uuid = db.Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_name = db.Column(db.String(32), nullable=False, index=True)
    phone_number = db.Column(db.String(8), nullable=True, index=True)
    mail = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=True)
    create_time = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    salutation = db.Column(db.String(32), nullable=True)
    birthday = db.Column(db.Date, nullable=True)
    nationality = db.Column(db.String(64), nullable=True)
    communication_language = db.Column(db.String(32), nullable=True)
    marketing_opt_out = db.Column(db.Boolean, nullable=False, default=False)
    brand_fortress = db.Column(db.Boolean, nullable=False, default=True)
    brand_parknshop = db.Column(db.Boolean, nullable=False, default=True)
    brand_watsons = db.Column(db.Boolean, nullable=False, default=True)
    brand_moneyback = db.Column(db.Boolean, nullable=False, default=True)

    addresses = db.relationship(
        'UserAddress', back_populates='user', lazy='dynamic', cascade='all, delete-orphan'
    )
    membership_row = db.relationship(
        'Membership', back_populates='user', uselist=False, cascade='all, delete-orphan'
    )
    points_logs = db.relationship(
        'MembershipPointsLog', back_populates='user', lazy='dynamic', cascade='all, delete-orphan'
    )

    def get_id(self):
        return str(self.user_uuid)

    @property
    def username(self):
        return self.user_name

    @username.setter
    def username(self, value):
        self.user_name = value

    @property
    def email(self):
        return self.mail

    @email.setter
    def email(self, value):
        self.mail = value

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f'<User {self.user_name}>'

    def avatar(self, size):
        digest = md5(self.mail.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {
                'reset_password': str(self.user_uuid),
                'exp': datetime.now(tz=timezone.utc) + timedelta(seconds=expires_in),
            },
            app.config['SECRET_KEY'],
            algorithm='HS256',
        )

    @staticmethod
    def verify_reset_password_token(token):
        try:
            payload = jwt.decode(
                token, app.config['SECRET_KEY'], algorithms=['HS256']
            )
            uid = uuid.UUID(payload['reset_password'])
        except Exception:
            return None
        return User.query.get(uid)


@login.user_loader
def load_user(id):
    try:
        uid = uuid.UUID(str(id))
    except ValueError:
        return None
    return User.query.get(uid)


class UserAddress(db.Model):
    __tablename__ = 'user_address'

    user_address_uuid = db.Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_uuid = db.Column(
        postgresql.UUID(as_uuid=True),
        db.ForeignKey('user.user_uuid', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    user = db.relationship('User', back_populates='addresses')
    user_address = db.Column(db.Text, nullable=False)
    unit = db.Column(db.String(64), nullable=True)
    floor = db.Column(db.String(32), nullable=True)
    building_street = db.Column(db.String(512), nullable=True)
    region = db.Column(db.String(32), nullable=True)
    district = db.Column(db.String(64), nullable=True)
    phone_number = db.Column(db.String(32), nullable=True)
    home_phone = db.Column(db.String(32), nullable=True)
    # 仅一個地址會被標記為預設（由應用邏輯維護）
    is_default = db.Column(db.Boolean, nullable=False, default=False, server_default=sa.text('false'))
    create_time = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    def formatted_line(self) -> str:
        parts = [
            self.region or '',
            self.district or '',
            self.building_street or '',
            self.floor or '',
            self.unit or '',
        ]
        return ' '.join(p for p in parts if p).strip()

    def __repr__(self) -> str:
        return f'<UserAddress {self.user_address_uuid}>'


class RegistrationVerificationCode(db.Model):
    """註冊驗證碼稽核：記錄 IP、郵箱、建立／過期／最後發送時間；完成註冊後標記 consumed。"""

    __tablename__ = 'registration_verification_code'

    id = db.Column(db.Integer, primary_key=True)
    client_ip = db.Column(db.String(45), nullable=False, index=True)
    code = db.Column(db.String(6), nullable=False)
    mail = db.Column(db.String(100), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    last_sent_at = db.Column(db.DateTime(timezone=True), nullable=False)
    consumed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f'<RegistrationVerificationCode {self.id} ip={self.client_ip} mail={self.mail}>'


class Membership(db.Model):
    __tablename__ = 'membership'

    user_uuid = db.Column(
        postgresql.UUID(as_uuid=True),
        db.ForeignKey('user.user_uuid', ondelete='CASCADE'),
        primary_key=True,
    )
    user = db.relationship('User', back_populates='membership_row')
    membership_point = db.Column(db.Integer, nullable=False, default=0)
    create_time = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    def __repr__(self) -> str:
        return f'<Membership user={self.user_uuid} points={self.membership_point}>'


class MembershipPointsLog(db.Model):
    __tablename__ = 'membership_points_log'

    points_log_uuid = db.Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_uuid = db.Column(
        postgresql.UUID(as_uuid=True),
        db.ForeignKey('user.user_uuid', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    user = db.relationship('User', back_populates='points_logs')

    transaction_time = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), index=True)
    retailer = db.Column(db.String(64), nullable=False)
    store_name = db.Column(db.String(128), nullable=False)
    transaction_amount_hkd = db.Column(db.Numeric(10, 2), nullable=False)
    base_points = db.Column(db.Integer, nullable=False, default=0)
    extra_points = db.Column(db.Integer, nullable=False, default=0)
    redeemed_points = db.Column(db.Integer, nullable=True)
    create_time = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    def __repr__(self) -> str:
        return f'<MembershipPointsLog {self.points_log_uuid} user={self.user_uuid}>'


class ProductCategory(db.Model):
    """貨物分類"""

    __tablename__ = 'product_categories'

    product_categories_id = db.Column(db.Integer, primary_key=True)
    product_categories_name = db.Column(db.String(128), nullable=False)
    create_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    products = db.relationship('ProductDetail', backref='category', lazy='dynamic')

    def __repr__(self) -> str:
        return f'<ProductCategory {self.product_categories_name}>'


class Supplier(db.Model):
    """供應商"""

    __tablename__ = 'supplier'

    supplier_id = db.Column(db.Integer, primary_key=True)
    supplier_name = db.Column(db.String(128), nullable=False)
    supplier_png = db.Column(db.String(256), nullable=True)
    create_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    products = db.relationship('ProductDetail', backref='supplier', lazy='dynamic')

    def __repr__(self) -> str:
        return f'<Supplier {self.supplier_name}>'


class ProductDetail(db.Model):
    """貨物詳情"""

    __tablename__ = 'product_details'

    product_categories_uuid = db.Column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_categories_id = db.Column(
        db.Integer, db.ForeignKey('product_categories.product_categories_id'), nullable=False
    )
    supplier_id = db.Column(
        db.Integer, db.ForeignKey('supplier.supplier_id'), nullable=False
    )
    product_name = db.Column(db.String(128), nullable=False)
    product_details = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    create_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f'<ProductDetail {self.product_name} ({self.product_categories_uuid})>'


class Delivery(db.Model):
    """商品配送表格"""

    __tablename__ = 'delivery'

    delivery_uuid = db.Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_uuid = db.Column(postgresql.UUID(as_uuid=True), nullable=False)  # Removed FK
    order_uuid = db.Column(postgresql.UUID(as_uuid=True), nullable=False)  # Removed FK
    deliver_time = db.Column(db.DateTime, nullable=True)
    create_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f'<Delivery {self.delivery_uuid}>'


class PaymentLog(db.Model):
    """支付日誌"""

    __tablename__ = 'payment_log'

    payment_uuid = db.Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_uuid = db.Column(postgresql.UUID(as_uuid=True), nullable=False)  # Removed FK
    order_uuid = db.Column(postgresql.UUID(as_uuid=True), nullable=False)  # Removed FK
    payment_methods = db.Column(db.String(64), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    state = db.Column(db.String(64), nullable=False)
    create_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f'<PaymentLog {self.payment_uuid}>'


class Refund(db.Model):
    """售後/退款表格"""

    __tablename__ = 'refund'

    refund_uuid = db.Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_uuid = db.Column(postgresql.UUID(as_uuid=True), nullable=False)  # Removed FK
    user_uuid = db.Column(postgresql.UUID(as_uuid=True), nullable=False)  # Removed FK
    create_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f'<Refund {self.refund_uuid}>'


class Evaluate(db.Model):
    """商品用後評價"""

    __tablename__ = 'evaluate'

    evaluate_uuid = db.Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_details_uuid = db.Column(postgresql.UUID(as_uuid=True), nullable=False)  # Removed FK
    user_uuid = db.Column(postgresql.UUID(as_uuid=True), nullable=False)  # Removed FK
    evaluate_txt = db.Column(db.Text, nullable=True)
    create_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f'<Evaluate {self.evaluate_uuid}>'
