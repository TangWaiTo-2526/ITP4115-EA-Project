from datetime import datetime
from decimal import Decimal
import uuid

from app import db, app
from app.models import User, Post, ProductCategory, Supplier, ProductDetail


app_context = app.app_context()
app_context.push()
db.drop_all()
db.create_all()

u1 = User(username='john', email='john@example.com')
u2 = User(username='susan', email='susan@example.com')
u1.set_password("P@ssw0rd")
u2.set_password("P@ssw0rd")
db.session.add(u1)
db.session.add(u2)
u1.follow(u2)
u2.follow(u1)

p1 = Post(body='my first post!', author=u1)
p2 = Post(body='my first post!', author=u2)
db.session.add(p1)
db.session.add(p2)

# Sample product data
pc = ProductCategory(
    product_categories_id=3,
    product_categories_name='飲品',
    create_time=datetime(2026, 1, 3, 9, 30, 0)
)

supplier = Supplier(
    supplier_id=1,
    supplier_name='可口可樂代理商',
    supplier_png='coke-supplier.png',
    create_time=datetime(2026, 1, 3, 10, 0, 0)
)

product = ProductDetail(
    product_categories_uuid=uuid.UUID('dd7660db-700d-4b1a-866a-16e1cd2ee4dd'),
    product_categories_id=pc.product_categories_id,
    supplier_id=supplier.supplier_id,
    product_name='可樂',
    product_details='330ml 罐裝，冰鎮更佳',
    price=Decimal('8.50'),
    create_time=datetime(2026, 1, 3, 11, 0, 0)
)

# Persist new records
db.session.add(pc)
db.session.add(supplier)
db.session.add(product)

db.session.commit()
