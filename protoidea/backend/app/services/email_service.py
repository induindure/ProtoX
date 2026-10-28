"""Sends account emails. With SMTP_HOST empty in .env, emails are printed to the
backend terminal instead (handy for local testing)."""
import smtplib
import ssl
from email.message import EmailMessage

from app.config import settings


def send_email(to: str, subject: str, text_body: str, html_body: str | None = None) -> None:
    if not settings.smtp_host:
        print("\n" + "=" * 70, flush=True)
        print(f"[DEV EMAIL - not actually sent]\nTo: {to}\nSubject: {subject}\n\n{text_body}", flush=True)
        print("=" * 70 + "\n", flush=True)
        return

    msg = EmailMessage()
    msg["From"] = settings.email_from or settings.smtp_user
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text_body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    context = ssl.create_default_context()
    if settings.smtp_port == 465:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, context=context, timeout=15) as server:
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            server.starttls(context=context)
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)


def send_verification_email(to: str, raw_token: str) -> None:
    link = f"{settings.frontend_url.rstrip('/')}/verify-email?token={raw_token}"
    hours = settings.verify_token_hours

    text = (
        "Welcome to ProtoX!\n\n"
        f"Confirm your email address by opening this link (valid for {hours} hours):\n\n"
        f"{link}\n\n"
        "If you didn't create a ProtoX account, you can ignore this email."
    )
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;padding:24px">
      <h2 style="color:#111">Welcome to ProtoX</h2>
      <p>Confirm your email address to start using your account.</p>
      <p style="margin:28px 0">
        <a href="{link}" style="background:#0f9b8e;color:#fff;padding:12px 22px;
           border-radius:10px;text-decoration:none;font-weight:bold">Verify my email</a>
      </p>
      <p style="color:#666;font-size:13px">This link is valid for {hours} hours.
         If you didn't create a ProtoX account, you can ignore this email.</p>
    </div>
    """
    send_email(to, "Verify your ProtoX account", text, html)