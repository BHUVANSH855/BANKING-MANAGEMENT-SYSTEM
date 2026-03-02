import smtplib
from email.mime.text import MIMEText

EMAIL = "yourbankemail@gmail.com"   # SAME gmail used above
APP_PASSWORD = "efdwnxnxtisuzlah"   # 16 chars, NO SPACES

msg = MIMEText("✅ Test email from Banking System")
msg["Subject"] = "Email Test"
msg["From"] = EMAIL
msg["To"] = EMAIL

server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()
server.login(EMAIL, APP_PASSWORD)
server.send_message(msg)
server.quit()

print("✅ EMAIL SENT SUCCESSFULLY")
