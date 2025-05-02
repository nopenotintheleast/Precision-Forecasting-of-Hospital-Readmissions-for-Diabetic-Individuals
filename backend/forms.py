from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User
from backend import db

class RegistrationForm(FlaskForm):
    username = StringField('Username', 
                         validators=[
                             DataRequired(),
                             Length(min=4, max=20, message="Username must be 4-20 characters")
                         ])
    email = StringField('Email',
                      validators=[
                          DataRequired(),
                          Email(message="Invalid email address")
                      ])
    first_name = StringField('First Name',
                           validators=[
                               DataRequired(),
                               Length(max=50)
                           ])
    last_name = StringField('Last Name',
                          validators=[
                              DataRequired(),
                              Length(max=50)
                          ])
    password = PasswordField('Password',
                           validators=[
                               DataRequired(),
                               Length(min=8, message="Password must be at least 8 characters"),
                               EqualTo('confirm_password', message="Passwords must match")
                           ])
    confirm_password = PasswordField('Confirm Password')
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose another.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please login instead.')

class LoginForm(FlaskForm):
    email = StringField('Email',
                      validators=[
                          DataRequired(),
                          Email()
                      ])
    password = PasswordField('Password',
                           validators=[
                               DataRequired()
                           ])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email',
                      validators=[
                          DataRequired(),
                          Email()
                      ])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password',
                           validators=[
                               DataRequired(),
                               Length(min=8)
                           ])
    confirm_password = PasswordField('Confirm New Password',
                                   validators=[
                                       DataRequired(),
                                       EqualTo('password')
                                   ])
    submit = SubmitField('Reset Password')