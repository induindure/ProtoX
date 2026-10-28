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


def send_verification_code(to: str, code: str) -> None:
    minutes = settings.verify_code_minutes

    text = (
        "Welcome to ProtoX!\n\n"
        f"Your verification code is: {code}\n\n"
        f"Enter it on the sign-up page. It expires in {minutes} minutes.\n\n"
        "If you didn't create a ProtoX account, you can ignore this email. "
        "Never share this code with anyone."
    )
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;padding:24px">
      <h2 style="color:#111">Welcome to ProtoX</h2>
      <p>Enter this code on the sign-up page to verify your email:</p>
      <p style="font-size:34px;font-weight:bold;letter-spacing:8px;color:#0f9b8e;
                background:#f0faf9;padding:16px;text-align:center;border-radius:12px">{code}</p>
      <p style="color:#666;font-size:13px">It expires in {minutes} minutes. Never share this code with anyone.
         If you didn't create a ProtoX account, you can ignore this email.</p>
    </div>
    """
    send_email(to, "Your ProtoX verification code", text, html)