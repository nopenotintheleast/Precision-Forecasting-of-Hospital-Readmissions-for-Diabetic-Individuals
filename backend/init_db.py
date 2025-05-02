from backend.app import app, db
from backend.models import User
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        # This will drop all tables and recreate them
        db.drop_all()
        db.create_all()
        
        if not User.query.filter_by(email='admin@diabetic.com').first():
            admin = User(
                username='admin',
                email='admin@diabetic.com',
                first_name='Admin',
                last_name='User',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Database initialized with admin user")

if __name__ == '__main__':
    init_db()