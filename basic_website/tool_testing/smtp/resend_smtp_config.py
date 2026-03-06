import smtplib
import os
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

# Config
SMTP_SERVER = "smtp.resend.com"
SMTP_PORT = 587
RESEND_API_KEY = os.getenv("API_KEY_RESEND")
SENDER = "onboarding@resend.dev"
RECEIVER = "aaroncoelhoirani@gmail.com"

# Create the email container
msg = EmailMessage()
msg.set_content("Sigma the front lines await your arrival... STRAP UP!")
msg.add_alternative("<p>Sigma the front lines await your arrival... <strong>STRAP UP</strong>!</p>", subtype='html')
msg['Subject'] = "README.MOFO"
msg['From'] = SENDER
msg['To'] = RECEIVER

# The standard SMTP flow
try:
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()  # Upgrade to secure connection
        server.login("resend", RESEND_API_KEY)
        server.send_message(msg)
    print("Email sent successfully!")
except Exception as e:
    print(f"Failed to send email: {e}")