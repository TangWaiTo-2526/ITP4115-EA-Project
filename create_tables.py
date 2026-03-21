from app import app, db
from app.models import *

with app.app_context():
    # Create all tables
    db.create_all()
    print("All tables created successfully!")