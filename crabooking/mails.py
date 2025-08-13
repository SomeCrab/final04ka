# crabooking/emails.py
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

def send_landlord_invite_email(user):
    to_email = (user.email or "").strip()
    if not to_email:
        return

    base_url = getattr(settings, "SITE_BASE_URL", "https://api.wiru.site").rstrip("/")
    promote_path = getattr(settings, "PROMOTE_SELF_PATH", "/promoteself/")
    promote_url = base_url + promote_path
    code = getattr(settings, "LANDLORD_INVITE_CODE", "")

    subject = "Welcome to Crabooking!"
    text = f"""Hi {user.username},

    Welcome to our Crabooking community — we’re happy you’ve joined us to find a place to stay!

    If you wish, you can activate the registration code at any time using this link and rise to the rank
    of venerable Landlord in order to rent out to the plebs!
    {promote_url}
    Activation code: {code}

    "So Long, and Thanks for all the Fish!"

    Your moderation loves you 🦀<3
    """

    html = f"""
        <!doctype html><meta charset="utf-8">
        <div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;line-height:1.5;">
        <h2 style="margin:0 0 12px;">Welcome to <b>Crabooking</b>, {user.username}!</h2>
        <p>We’re happy you’ve joined our nimble community to find a place to stay 🦀</p>
        <p>
        If you wish, you can activate the registration code at any time using this link and rise to the rank
            of venerable <b>Landlord</b> in order to rent out to the plebs!</p>
        <p><a href="{promote_url}" style="color:#0b5fff;">{promote_url}</a></p>
        <p>Activation code: <code style="font-size:1.05em;">{code}</code></p>
        <blockquote style="margin:16px 0;color:#555;">So Long, and Thanks for all the Fish!</blockquote>
        <p>Your moderation loves you &lt;3</p><br><br>

        <p>PS if it wasn't you - no worriers, just ignore that message.</p>
        </div>
    """

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@wiru.site")
    msg = EmailMultiAlternatives(subject=subject, body=text, from_email=from_email, to=[to_email])
    msg.attach_alternative(html, "text/html")
    try:
        msg.send()
    except Exception:
        pass
