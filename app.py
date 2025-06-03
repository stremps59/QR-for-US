
import os
import base64
import io
from flask import Flask, request, jsonify
from flask_cors import CORS
import qrcode
from PIL import Image
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib

app = Flask(__name__)
CORS(app)

def generate_qr(data, color="black", center_image=None):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=color, back_color="white").convert("RGB")

    if center_image:
        try:
            logo = Image.open(io.BytesIO(requests.get(center_image).content))
            basewidth = 100
            wpercent = basewidth / float(logo.size[0])
            hsize = int((float(logo.size[1]) * float(wpercent)))
            logo = logo.resize((basewidth, hsize), Image.ANTIALIAS)
            pos = ((img.size[0] - logo.size[0]) // 2, (img.size[1] - logo.size[1]) // 2)
            img.paste(logo, pos, mask=logo if logo.mode == 'RGBA' else None)
        except Exception as e:
            print(f"Error processing center image: {e}")

    return img

@app.route("/generate_qr", methods=["POST"])
def generate_qr_code():
    data = request.json
    qr_data = data.get("data")
    email = data.get("email")
    color = data.get("color", "black")
    center_image = data.get("center_image")

    if not qr_data or not email:
        return jsonify({"error": "Missing data or email"}), 400

    img = generate_qr(qr_data, color=color, center_image=center_image)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    img_bytes = buffer.read()

    try:
        send_email(email, img_bytes)
        return jsonify({"message": "QR code generated and sent via email"}), 200
    except Exception as e:
        print(f"Error sending email: {e}")
        return jsonify({"error": str(e)}), 500

def send_email(recipient, img_bytes):
    mailgun_domain = os.getenv("MAILGUN_DOMAIN")
    mailgun_api_key = os.getenv("MAILGUN_API_KEY")

    if not mailgun_domain or not mailgun_api_key:
        raise ValueError("Mailgun configuration is missing.")

    response = requests.post(
        f"https://api.mailgun.net/v3/{mailgun_domain}/messages",
        auth=("api", mailgun_api_key),
        files={"attachment": ("qr_code.png", img_bytes)},
        data={
            "from": f"QR for US <no-reply@{mailgun_domain}>",
            "to": [recipient],
            "subject": "Your QR Code from QR for US™",
            "text": "Thanks for using QR for US™! Your QR code is attached and ready to use.

To scan: print or share the image.
To reuse or reprint: this code will stay active for 30 days.

Need changes? You can request a Do Over within 24 hours.

Thanks again,
QR for US™"
        },
    )

    if response.status_code != 200:
        raise Exception(f"Mailgun API error: {response.text}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
