import os
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import joblib
import pandas as pd
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from flask_wtf.csrf import CSRFProtect
import secrets
import string

# Initialize Flask app with absolute paths
app = Flask(__name__, 
            template_folder=os.path.abspath('../frontend/templates'),
            static_folder=os.path.abspath('../frontend/static'))

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost:5432/diabetic_readmission')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Fixed typo in 'TRACK_MODIFICATIONS'

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
csrf = CSRFProtect(app)

# Get absolute paths to model files
BASE_DIR = Path(__file__).parent.parent
MODEL_PATH = os.path.join(BASE_DIR, 'ml_model', 'readmission_model.pkl')
METADATA_PATH = os.path.join(BASE_DIR, 'ml_model', 'model_metadata.pkl')

# --- FORMS ---
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password',
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password', 
                                   validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

class UpdateEmailForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_email = StringField('New Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Update Email')

class DeleteAccountForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    confirm_delete = BooleanField('I understand this action is irreversible', 
                                validators=[DataRequired()])
    submit = SubmitField('Delete Account')

# --- MODELS ---
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    reset_token = db.Column(db.String(100))
    reset_token_expiration = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self):
        self.reset_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        self.reset_token_expiration = datetime.utcnow() + timedelta(seconds=3600)
        db.session.commit()
        return self.reset_token

    @staticmethod
    def verify_reset_token(token):
        return User.query.filter_by(reset_token=token).filter(
            User.reset_token_expiration > datetime.utcnow()).first()

# --- AUTHENTICATION ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # Changed from db.session.get to User.query.get

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        
        flash('Invalid email or password', 'danger')
    
    return render_template('auth/login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        existing_user = User.query.filter((User.email == form.email.data) | 
                                        (User.username == form.username.data)).first()
        if existing_user:
            flash('Email or username already exists', 'danger')
            return redirect(url_for('register'))
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = ResetPasswordRequestForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            reset_url = url_for('reset_password', token=token, _external=True)
            flash(f'Password reset link has been sent to {user.email}.', 'info')
            print(f"Password reset link (for development): {reset_url}")
            return redirect(url_for('login'))
        
        flash('If this email exists, you will receive a password reset link', 'info')
    
    return render_template('auth/reset_request.html', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    user = User.verify_reset_token(token)
    if not user:
        flash('Invalid or expired token', 'danger')
        return redirect(url_for('reset_password_request'))
    
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.reset_token = None
        user.reset_token_expiration = None
        db.session.commit()
        flash('Your password has been reset.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/reset_password.html', form=form)

# --- DASHBOARD ROUTES ---
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    try:
        viz_dir = os.path.join(app.static_folder, 'visualizations')
        viz_files = []
        if os.path.exists(viz_dir):
            viz_files = [f for f in os.listdir(viz_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        return render_template('dashboard.html', visualizations=viz_files)
    except Exception as e:
        app.logger.error(f"Dashboard error: {str(e)}")
        flash('An error occurred while loading the dashboard', 'danger')
        return redirect(url_for('login'))

# --- PREDICTION ROUTES ---
@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    class PredictionForm(FlaskForm):
        pass
    
    form = PredictionForm()
    
    if request.method == 'POST':
        try:
            # Load model and metadata with validation
            model = joblib.load(MODEL_PATH)
            metadata = joblib.load(METADATA_PATH)
            
            # Verify required metadata exists
            required_metadata = ['preprocessor', 'numeric_features', 'categorical_features', 'threshold']
            for key in required_metadata:
                if key not in metadata:
                    raise ValueError(f"Missing required metadata: {key}")
            
            # Create input dictionary with strict type handling
            input_data = {}
            
            # Process NUMERIC features
            for field in metadata['numeric_features']:
                try:
                    raw_value = request.form.get(field, '0').strip()
                    input_data[field] = float(raw_value) if raw_value else 0.0
                except (ValueError, TypeError):
                    input_data[field] = 0.0
                    app.logger.warning(f"Invalid numeric input for {field}, using 0.0")
            
            # Process CATEGORICAL features
            categorical_values = metadata.get('categorical_values', {})
            for field in metadata['categorical_features']:
                raw_value = request.form.get(field, '').strip()
                
                if not raw_value:
                    input_data[field] = 'missing'
                    continue
                
                known_categories = categorical_values.get(field, [])
                if known_categories and raw_value not in known_categories:
                    app.logger.warning(f"Unknown category {raw_value} for {field}, using 'unknown'")
                    input_data[field] = 'unknown'
                else:
                    input_data[field] = raw_value
            
            # Create DataFrame with exact feature order
            all_features = metadata['numeric_features'] + metadata['categorical_features']
            input_df = pd.DataFrame({col: [input_data.get(col)] for col in all_features})
            
            # Type conversion
            for col in metadata['numeric_features']:
                input_df[col] = pd.to_numeric(input_df[col], errors='coerce').fillna(0)
            
            for col in metadata['categorical_features']:
                input_df[col] = input_df[col].astype(str).str.strip()
                input_df[col] = input_df[col].replace({'nan': 'missing', '': 'missing'})
            
            # Preprocessing
            try:
                X = metadata['preprocessor'].transform(input_df)
                
                if X.shape[1] != model.n_features_in_:
                    raise ValueError(
                        f"Feature mismatch: expected {model.n_features_in_} features, "
                        f"got {X.shape[1]} after preprocessing"
                    )
            except Exception as e:
                app.logger.error(f"Preprocessing failed: {str(e)}\nInput data: {input_df.to_dict()}")
                flash('Data processing error. Please check your inputs.', 'danger')
                return redirect(url_for('predict'))
            
            # Make prediction
            try:
                probability = float(model.predict_proba(X)[0, 1])
                threshold = float(metadata['threshold'])
                
                # Prepare feature importance data
                feature_importance = {}
                if hasattr(model, 'feature_importances_'):
                    # Sort features by importance and get top 5
                    features_with_importance = sorted(
                        zip(all_features, model.feature_importances_),
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]
                    feature_importance = {k: float(v) for k, v in features_with_importance}
                
                result = {
                    'probability': f"{probability:.1%}",
                    'prediction': 'High Risk' if probability >= threshold else 'Low Risk',
                    'threshold': f"{threshold:.1%}",
                    'feature_importance': feature_importance
                }
                
                flash('Prediction successful!', 'success')
                return render_template('predict.html', form=form, result=result)
                
            except Exception as e:
                app.logger.error(f"Prediction failed: {str(e)}")
                flash('Prediction calculation error. Please try again.', 'danger')
                return redirect(url_for('predict'))
            
        except Exception as e:
            app.logger.error(f"System error: {str(e)}", exc_info=True)
            flash('System error occurred. Please contact support.', 'danger')
            return redirect(url_for('predict'))
    
    # GET request - ensure result is None and feature_importance is an empty dict
    return render_template('predict.html', form=form, result={'feature_importance': {}})

# --- VISUALIZATION ROUTES ---
@app.route('/visualizations')
@login_required
def visualizations():
    try:
        viz_dir = os.path.join(app.static_folder, 'visualizations')
        viz_files = []
        if os.path.exists(viz_dir):
            viz_files = [f for f in os.listdir(viz_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        return render_template('visualizations.html', visualizations=viz_files)
    except Exception as e:
        app.logger.error(f"Visualizations error: {str(e)}")
        flash('An error occurred while loading visualizations', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/visualization/<filename>')
@login_required
def view_visualization(filename):
    try:
        return send_from_directory(os.path.join(app.static_folder, 'visualizations'), filename)
    except Exception as e:
        app.logger.error(f"Visualization error: {str(e)}")
        flash('The requested visualization could not be found', 'danger')
        return redirect(url_for('visualizations'))

# --- PROFILE ROUTES ---
@app.route('/profile')
@login_required
def profile():
    try:
        # Verify the user is authenticated
        if not current_user.is_authenticated:
            flash('Please log in to view your profile', 'danger')
            return redirect(url_for('login'))

        # Create form instances for the modals
        change_password_form = ChangePasswordForm()
        update_email_form = UpdateEmailForm()
        delete_account_form = DeleteAccountForm()

        # Safely get user data with fallback values
        user_data = {
            'first_name': getattr(current_user, 'first_name', 'Not provided'),
            'last_name': getattr(current_user, 'last_name', 'Not provided'),
            'email': getattr(current_user, 'email', 'Not provided'),
            'username': getattr(current_user, 'username', 'Not provided'),
            'created_at': current_user.created_at.strftime('%B %d, %Y') if hasattr(current_user, 'created_at') and current_user.created_at else 'Unknown date'
        }

        return render_template(
            'profile.html',
            user=user_data,
            change_password_form=change_password_form,
            update_email_form=update_email_form,
            delete_account_form=delete_account_form
        )
    except Exception as e:
        app.logger.error(f"Error loading profile: {str(e)}", exc_info=True)
        flash('An error occurred while loading your profile. Please try again.', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        try:
            if not current_user.check_password(form.current_password.data):
                flash('Current password is incorrect', 'danger')
                return redirect(url_for('profile') + '#changePasswordModal')
            
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password updated successfully', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            app.logger.error(f"Password change error: {str(e)}")
            flash('An error occurred while changing your password', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", 'danger')
    
    return redirect(url_for('profile') + '#changePasswordModal')

@app.route('/profile/update-email', methods=['POST'])
@login_required
def update_email():
    form = UpdateEmailForm()
    
    if form.validate_on_submit():
        try:
            if not current_user.check_password(form.current_password.data):
                flash('Current password is incorrect', 'danger')
                return redirect(url_for('profile') + '#updateEmailModal')
            
            existing_user = User.query.filter_by(email=form.new_email.data).first()
            if existing_user:
                flash('Email already in use', 'danger')
                return redirect(url_for('profile') + '#updateEmailModal')
            
            current_user.email = form.new_email.data.lower()
            db.session.commit()
            flash('Email updated successfully', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            app.logger.error(f"Email update error: {str(e)}")
            flash('An error occurred while updating your email', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", 'danger')
    
    return redirect(url_for('profile') + '#updateEmailModal')

@app.route('/profile/delete-account', methods=['POST'])
@login_required
def delete_account():
    form = DeleteAccountForm()
    
    if form.validate_on_submit():
        try:
            if not current_user.check_password(form.current_password.data):
                flash('Current password is incorrect', 'danger')
                return redirect(url_for('profile') + '#deleteAccountModal')
            
            db.session.delete(current_user)
            db.session.commit()
            logout_user()
            flash('Your account has been permanently deleted', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            app.logger.error(f"Account deletion error: {str(e)}")
            flash('An error occurred while deleting your account', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", 'danger')
    
    return redirect(url_for('profile') + '#deleteAccountModal')

# --- ERROR HANDLERS ---
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

# --- FAVICON HANDLER ---
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.static_folder, 'images'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

# --- DATABASE INITIALIZATION ---
def init_db():
    with app.app_context():
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

# --- COMMAND LINE INTERFACE ---
def init_db_command():
    """Initialize the database."""
    init_db()
    print("Database initialized")

app.cli.add_command(init_db_command, name='init-db')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
