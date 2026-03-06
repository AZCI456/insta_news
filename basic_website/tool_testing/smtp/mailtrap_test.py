# Looking to send emails in production? Check out our Email API/SMTP product!
import smtplib

sender = "Private Person <solig0v1nok3@maximail.vip>"
receiver = "A Test User <solig0v1nok3@maximail.vip>"

message = f"""\
Subject: Hi Mailtrap
To: {receiver}
From: {sender}

This is a test e-mail message."""

with smtplib.SMTP("sandbox.smtp.mailtrap.io", 2525) as server:
    server.starttls()
    server.login("2c2f8d0c7d5f24", "e7449c01d7da53")
    server.sendmail(sender, receiver, message)