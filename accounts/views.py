from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from .forms import CustomUserCreationForm, EmailAuthenticationForm
from .models import CustomUser
from .utils import send_verification_email
from django.utils import timezone
from datetime import timedelta



def signup_view(request):
    if request.user.is_authenticated:
        return redirect('core')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_verification_email(request, user)
            messages.success(
                request,
                "Account created! Please check your email and click the verification link to activate your account."
            )
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})


def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_email_verified = True
        user.is_active = True
        user.save()
        messages.success(request,
                         "Email verified successfully! You can now log in.")
        return redirect('login')
    else:
        messages.error(request, "Invalid verification link.")
        return redirect('signup')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core')

    if request.method == 'POST':
        form = EmailAuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Logged in successfully.")
            return redirect('core')
        else:
            # Check if the user exists but email is not verified
            email = request.POST.get('email')
            if email:
                try:
                    user = CustomUser.objects.get(email=email)
                    if not user.is_email_verified:
                        messages.warning(
                            request,
                            "Your email address is not verified. Please check your email for the verification link."
                        )
                        # Store the email in session for resend functionality
                        request.session['unverified_email'] = email
                except CustomUser.DoesNotExist:
                    pass  # User doesn't exist, let the form handle the error
    else:
        form = EmailAuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})

def resend_verification_email(request):
    if request.method == 'POST':
        email = request.POST.get('email') or request.session.get(
            'unverified_email')

        # Simple rate limiting - check if we sent an email recently
        last_sent_key = f'verification_sent_{email}'
        last_sent = request.session.get(last_sent_key)

        if last_sent:
            last_sent_time = timezone.datetime.fromisoformat(last_sent)
            if timezone.now() - last_sent_time < timedelta(minutes=2):
                messages.warning(
                    request,
                    "Please wait a few minutes before requesting another verification email."
                )
                return redirect('login')

        if email:
            try:
                user = CustomUser.objects.get(email=email)
                if not user.is_email_verified:
                    send_verification_email(request, user)
                    # Record when we sent the email
                    request.session[last_sent_key] = timezone.now().isoformat()
                    messages.success(
                        request,
                        "Verification email sent! Please check your inbox."
                    )
                else:
                    messages.info(request, "This email is already verified.")
            except CustomUser.DoesNotExist:
                messages.error(request,
                               "No account found with this email address.")
        else:
            messages.error(request, "Please provide an email address.")

    return redirect('login')


def logout_view(request):
    logout(request)
    return redirect('login')