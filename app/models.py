
from datetime import datetime, timedelta, timezone
from hashlib import md5
import uuid

from app import app, db, login
import jwt

from flask_login import UserMixin
from sqlalchemy.dialects import postgresql

from werkzeug.security import generate_password_hash, check_password_hash


followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __repr__(self) -> str:
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, followers.c.followed_id == Post.user_id
        ).filter(followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode({"reset_password": self.id,
                           "exp": datetime.now(tz=timezone.utc) + timedelta(seconds=expires_in)},
                          app.config["SECRET_KEY"], algorithm="HS256")

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config["SECRET_KEY"], algorithms="HS256")[
                "reset_password"]
        except:           
            return None
        return User.query.get(id)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self) -> str:
        return f'<Post {self.body}>'


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
