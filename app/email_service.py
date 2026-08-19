import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import logging
from app.config import settings

logger = logging.getLogger(__name__)

async def send_alert(admin_email: str, subject: str, details: str):
    """Send intrusion/security alert email to admin. Non-blocking."""
    try:
        if not settings.SMTP_HOST or settings.SMTP_HOST == 'smtp.gmail.com' and settings.SMTP_USER == 'your-email@gmail.com':
            logger.warning(f"SMTP not configured. Alert logged: {subject} - {details}")
            return
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USER
        msg['To'] = admin_email
        msg['Subject'] = f"[SECURITY ALERT] {subject}"
        msg.attach(MIMEText(f"Security Alert Details:\n\n{details}", 'plain'))
        await aiosmtplib.send(msg, hostname=settings.SMTP_HOST, port=settings.SMTP_PORT, username=settings.SMTP_USER, password=settings.SMTP_PASSWORD, use_tls=False, start_tls=True)
        logger.info(f"Alert email sent to {admin_email}")
    except Exception as e:
        logger.error(f"Failed to send alert email: {e}")

async def send_report(recipient: str, file_path: str, subject: str = "Attendance Report"):
    """Send attendance report Excel file via email."""
    try:
        if not settings.SMTP_HOST or settings.SMTP_USER == 'your-email@gmail.com':
            logger.warning(f"SMTP not configured. Report for {recipient} saved at {file_path}")
            return
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USER
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText("Please find the attendance report attached.", 'plain'))
        with open(file_path, 'rb') as f:
            part = MIMEBase('application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{file_path.split("/")[-1]}"')
            msg.attach(part)
        await aiosmtplib.send(msg, hostname=settings.SMTP_HOST, port=settings.SMTP_PORT, username=settings.SMTP_USER, password=settings.SMTP_PASSWORD, use_tls=False, start_tls=True)
        logger.info(f"Report sent to {recipient}")
    except Exception as e:
        logger.error(f"Failed to send report: {e}")
