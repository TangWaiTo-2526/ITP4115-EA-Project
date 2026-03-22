from threading import Thread
from flask import render_template
from flask_mail import Message
from app import app, mail


def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception:
            app.logger.exception('非同步郵件發送失敗')


def _smtp_sender():
    return (
        app.config.get('MAIL_DEFAULT_SENDER')
        or app.config.get('MAIL_USERNAME')
        or app.config['ADMINS'][0]
    )


def send_email(
    subject,
    sender,
    recipients,
    text_body,
    html_body,
    async_send=True,
):
    msg = Message(subject, sender=sender or _smtp_sender(), recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    if async_send:
        Thread(target=send_async_email, args=(app, msg)).start()
    else:
        with app.app_context():
            mail.send(msg)


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('[PNS 網購] 重設密碼',
               sender=_smtp_sender(),
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt.j2',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html.j2',
                                         user=user, token=token))


def send_registration_verification_email(to_mail, user_name, code):
    send_email(
        '[PNS 網購] 註冊驗證碼',
        sender=_smtp_sender(),
        recipients=[to_mail],
        text_body=render_template(
            'email/register_verify.txt.j2',
            user_name=user_name,
            code=code,
        ),
        html_body=render_template(
            'email/register_verify.html.j2',
            user_name=user_name,
            code=code,
        ),
        async_send=True,
    )
