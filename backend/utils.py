from flask_mail import Message
from backend import mail, app
from flask import url_for

def send_reset_email(user, token):
    msg = Message('Password Reset Request',
                 sender='noreply@diabeticapp.com',
                 recipients=[user.email])
    msg.body = f'''To reset your password, visit:
{url_for('auth.reset_token', token=token, _external=True)}

If you did not request this, ignore this email.
'''
    mail.send(msg)

def send_verification_email(user, token):
    msg = Message('Verify Your Email',
                 sender='noreply@diabeticapp.com',
                 recipients=[user.email])
    msg.body = f'''Verify your email:
{url_for('auth.verify_email', token=token, _external=True)}

If you didn’t create an account, ignore this.
'''
    mail.send(msg)