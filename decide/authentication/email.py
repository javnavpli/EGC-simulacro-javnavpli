from django.core.mail import EmailMultiAlternatives, BadHeaderError
from django.template.loader import get_template
from django.template import Context

def send_mail_with_token(to_email, token):
    subject = 'Decide - Correo de prueba'
    from_email = 'Decide <do_not_reply@example.com>'

    cont = { 
        'usuario': 'username de prueba',
        'token': token
    }

    msg_plain = get_template('email.txt').render(cont)
    msg_html = get_template('email.html').render(cont)

    try:
        msg = EmailMultiAlternatives(subject, msg_plain, from_email, [to_email])
        msg.attach_alternative(msg_html, "text/html")
        msg.send()
    except BadHeaderError:
        pass
    