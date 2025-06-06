import os
import io
import uuid
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from qrcode_styled.main import QRCode  # ← corrected import
from PIL import Image

app = Flask(__name__)
CORS(app)

# Load environment variables with default values
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY", "")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN", "")
MAILGUN_FROM = os.getenv("MAILGUN_FROM", f"mailgun@{MAILGUN_DOMAIN}")

@app.route("/")
def home():
    return "QR for US backend is running"

@app.route("/generate_qr", methods=["POST"])
def generate_qr():
    try:
        data = request.json or {}
        fields = data.get("data", {}).get("fields", [])

        def get_value(label):
            for field in fields:
                if field.get("label") == label:
                    return field.get("value")
            return ""

        email = get_value("Your Email")
        url = get_value("Website or Link URL")

        if not email or not url:
            return jsonify({"error": "Missing email or URL"}), 400

        # Generate QR code image
        qr = QRCode()
        qr.add_data(url)
        img = qr.make_image()

        # Save image to memory
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        img_data = buffer.read()

        # Send email via Mailgun
        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            files=[("attachment", ("qr_code.png", img_data))],
            data={
                "from": MAILGUN_FROM,
                "to": email,
                "subject": "Your QR for US™ Code",
                "text": "Thanks for using QR for US™! Your QR code is attached as a PNG image.",
            }
        )

        if response.status_code != 200:
            return jsonify({"error": "Mailgun error", "details": response.text}), 500

        return jsonify({"message": "QR code generated and email sent."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

