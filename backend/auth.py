from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, AuditLog, db
from forms import RegistrationForm, LoginForm, ResetPasswordRequestForm, ResetPasswordForm
from datetime import datetime
from utils import send_reset_email, send_verification_email
import uuid
from user_agents import parse

auth_bp = Blueprint('auth', __name__, template_folder='../frontend/templates/auth')

def log_audit(action, user_id=None, details=None):
    """Log user activities to database"""
    try:
        user_agent = parse(request.user_agent.string)
        log = AuditLog(
            user_id=user_id or (current_user.id if current_user.is_authenticated else None),
            action=action,
            ip_address=request.remote_addr,
            user_agent=str(user_agent),
            details=details or {}
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Audit log failed: {str(e)}")

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Check if user exists
            if User.query.filter_by(email=form.email.data).first():
                flash('Email already registered', 'danger')
                return redirect(url_for('auth.register'))
            
            # Create new user
            user = User(
                username=form.username.data,
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                password_hash=generate_password_hash(form.password.data),
                is_active=True
            )
            
            # Generate verification token
            verification_token = str(uuid.uuid4())
            user.verification_token = verification_token
            user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
            
            db.session.add(user)
            db.session.commit()
            
            # Send verification email
            send_verification_email(user, verification_token)
            
            log_audit('register', user.id, {'email': user.email})
            
            flash('Registration successful! Please check your email to verify your account.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration error: {str(e)}")
            flash('Registration failed. Please try again.', 'danger')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first()
            
            if not user or not check_password_hash(user.password_hash, form.password.data):
                flash('Invalid email or password', 'danger')
                log_audit('login_failed', None, {'email': form.email.data})
                return redirect(url_for('auth.login'))
                
            if not user.is_active:
                flash('Account disabled. Contact support.', 'danger')
                return redirect(url_for('auth.login'))
                
            login_user(user, remember=form.remember.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            log_audit('login_success', user.id)
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Login error: {str(e)}")
            flash('Login failed. Please try again.', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    log_audit('logout', current_user.id)
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            reset_token = str(uuid.uuid4())
            user.reset_token = reset_token
            user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            send_reset_email(user, reset_token)
            log_audit('password_reset_request', user.id)
        
        flash('If your email exists, you will receive reset instructions', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_request.html', form=form)

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    user = User.query.filter_by(reset_token=token).first()
    if not user or user.reset_token_expires < datetime.utcnow():
        flash('Invalid or expired token', 'danger')
        return redirect(url_for('auth.reset_password_request'))
        
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password_hash = generate_password_hash(form.password.data)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()
        
        log_audit('password_reset_success', user.id)
        flash('Your password has been updated!', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form)

@auth_bp.route('/verify_email/<token>')
def verify_email(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    user = User.query.filter_by(verification_token=token).first()
    if not user or user.verification_token_expires < datetime.utcnow():
        flash('Invalid or expired verification link', 'danger')
        return redirect(url_for('auth.login'))
        
    user.email_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.session.commit()
    
    log_audit('email_verified', user.id)
    flash('Email verification successful! You can now login.', 'success')
    return redirect(url_for('auth.login'))