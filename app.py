
import os
import io
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
import qrcode
from qrcode.image.pil import PilImage
from PIL import Image
import requests

app = Flask(__name__)
CORS(app)

MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
FROM_EMAIL = f"QR for US <qrforus@{MAILGUN_DOMAIN}>"

def generate_qr_code(data, fill_color="black", back_color="white"):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(image_factory=PilImage, fill_color=fill_color, back_color=back_color)
    return img

def send_email(recipient, subject, body, qr_bytes):
    print("send_email triggered")
    print(f"Sending email to: {recipient}")
    try:
        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            files=[("attachment", ("qr_code.png", qr_bytes, "image/png"))],
            data={
                "from": FROM_EMAIL,
                "to": recipient,
                "subject": subject,
                "text": body
            }
        )
        print(f"Mailgun response status: {response.status_code}")
        print(f"Mailgun response body: {response.text}")
    except Exception as e:
        print("Error sending email:", str(e))
        traceback.print_exc()

@app.route("/generate_qr", methods=["POST"])
def generate_qr():
    try:
        data = request.json
        print("Received data:", data)

        qr_data = data.get("qr_data")
        recipient_email = data.get("email")
        fill_color = data.get("color", "black")
        back_color = data.get("background", "white")

        if not qr_data or not recipient_email:
            return jsonify({"error": "Missing qr_data or email"}), 400

        img = generate_qr_code(qr_data, fill_color, back_color)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)

        send_email(
            recipient=recipient_email,
            subject="Your QR Code from QR for US",
            body="Attached is your generated QR code. Scan or click to visit the destination.",
            qr_bytes=img_byte_arr.read()
        )

        return jsonify({"message": "QR code generated and email sent successfully"}), 200
    except Exception as e:
        print("Error in generate_qr:", str(e))
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=True)
