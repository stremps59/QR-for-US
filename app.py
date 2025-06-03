from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import qrcode
import os
import uuid
from PIL import Image
import requests
from io import BytesIO
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

app = Flask(__name__)
CORS(app)

MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
SENDER_EMAIL = "QR for US <qrforus@{}>".format(MAILGUN_DOMAIN)

@app.route("/generate_qr", methods=["POST"])
def generate_qr():
    data = request.json

    url = data.get("url")
    email = data.get("email")
    filename = f"{uuid.uuid4()}.png"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )

    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

    img_path = f"/tmp/{filename}"
    img.save(img_path)

    if email:
        send_email(email, img_path, filename, url)

    return jsonify({"message": "QR code generated", "filename": filename})

def send_email(recipient_email, attachment_path, filename, do_over_url):
    sender_email = SENDER_EMAIL

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = "Your QR for US™ code is ready!"

    body = MIMEText("""Thanks for using QR for US™!

Your QR code is attached and ready to use. You can:
• Print it
• Share it
• Link it anywhere online

Need to make a change?
You can request a “Do Over” here:
{}

Your code will be stored for 30 days (or longer with a subscription).

Thanks again,
QR for US™
""".format(do_over_url), "plain")

    message.attach(body)

    with open(attachment_path, "rb") as f:
        part = MIMEApplication(f.read(), Name=filename)
        part['Content-Disposition'] = f'attachment; filename="{filename}"'
        message.attach(part)

    response = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        files=[("attachment", (filename, open(attachment_path, "rb").read()))],
        data={
            "from": sender_email,
            "to": recipient_email,
            "subject": "Your QR for US™ code is ready!",
            "text": body.get_payload()
        }
    )

    print("Mailgun response:", response.status_code, response.text)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
