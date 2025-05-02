from flask_login import UserMixin
from datetime import datetime, timedelta
from backend.app import db  # Changed this line only
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from sqlalchemy.dialects.postgresql import UUID, JSONB

class User(db.Model, UserMixin):
    """
    User model for PostgreSQL with enhanced security features
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    last_password_change = db.Column(db.DateTime, default=datetime.utcnow)
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime)
    profile_data = db.Column(JSONB)  # For storing additional user data

    # Password reset fields
    reset_token = db.Column(db.String(100))
    reset_token_expires = db.Column(db.DateTime)

    # Email verification fields
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100))
    verification_token_expires = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.is_admin is None:
            self.is_admin = False
        if self.public_id is None:
            self.public_id = uuid.uuid4()

    def set_password(self, password):
        """Create hashed password"""
        self.password_hash = generate_password_hash(
            password,
            method='pbkdf2:sha256',
            salt_length=16
        )
        self.last_password_change = datetime.utcnow()

    def check_password(self, password):
        """Check hashed password"""
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self, expires_sec=1800):
        """Generate password reset token"""
        self.reset_token = str(uuid.uuid4())
        self.reset_token_expires = datetime.utcnow() + timedelta(seconds=expires_sec)
        db.session.commit()
        return self.reset_token

    def verify_reset_token(token):
        """Verify password reset token"""
        user = User.query.filter_by(reset_token=token).first()
        if user and user.reset_token_expires > datetime.utcnow():
            return user
        return None

    def get_verification_token(self, expires_sec=86400):
        """Generate email verification token"""
        self.verification_token = str(uuid.uuid4())
        self.verification_token_expires = datetime.utcnow() + timedelta(seconds=expires_sec)
        db.session.commit()
        return self.verification_token

    def verify_email_token(token):
        """Verify email verification token"""
        user = User.query.filter_by(verification_token=token).first()
        if user and user.verification_token_expires > datetime.utcnow():
            user.email_verified = True
            user.verification_token = None
            user.verification_token_expires = None
            db.session.commit()
            return user
        return None

    def record_failed_login(self):
        """Record failed login attempt and lock account if needed"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
        db.session.commit()

    def reset_login_attempts(self):
        """Reset failed login attempts"""
        self.failed_login_attempts = 0
        self.account_locked_until = None
        db.session.commit()

    def is_account_locked(self):
        """Check if account is currently locked"""
        if self.account_locked_until and self.account_locked_until > datetime.utcnow():
            return True
        if self.account_locked_until and self.account_locked_until <= datetime.utcnow():
            self.reset_login_attempts()
        return False

    def __repr__(self):
        return f'<User {self.username}>'

class AuditLog(db.Model):
    """
    Audit log for tracking user activities
    """
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    details = db.Column(JSONB)

    user = db.relationship('User', backref='audit_logs')

class Prediction(db.Model):
    """
    Store prediction history for users
    """
    __tablename__ = 'predictions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    input_data = db.Column(JSONB, nullable=False)
    prediction_result = db.Column(JSONB, nullable=False)
    probability = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    model_version = db.Column(db.String(50))

    user = db.relationship('User', backref='predictions')

    def __repr__(self):
        return f'<Prediction {self.id} by User {self.user_id}>'