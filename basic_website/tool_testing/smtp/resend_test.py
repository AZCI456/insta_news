import resend
import os
from dotenv import load_dotenv
load_dotenv()

resend.api_key = os.getenv("API_KEY_RESEND")

r = resend.Emails.send({
  "from": "onboarding@resend.dev",
  "to": "bruvsky@gmail.com",
  "subject": "README.MOFO",
  "html": "<p>Sigma the front lines await your arrival... <strong>STRAP UP</strong>!</p>"
})
