from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.urls import reverse


def send_verification_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    verification_url = request.build_absolute_uri(
        reverse('verify_email', kwargs={'uidb64': uid, 'token': token})
    )

    subject = 'Verify your email address'

    # Create plain text version
    text_content = f"""
    Welcome {user.email}!

    Thank you for creating an account. Please click the link below to verify your email address:

    {verification_url}

    If you didn't create this account, please ignore this email.
    """

    # Create HTML version
    html_content = render_to_string('accounts/verification_email.html', {
        'user': user,
        'verification_url': verification_url,
    })

    # Create email with both plain text and HTML versions
    msg = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL or 'webmaster@localhost',
        [user.email]
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()