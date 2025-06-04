import os
import io
import qrcode
from PIL import Image
from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import requests

app = Flask(__name__)
CORS(app)

MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
FROM_EMAIL = "QR for US <qrforus@sandboxa061d0b8830b4e8a96f9260e7e6ea8be.mailgun.org>"

@app.route("/generate_qr", methods=["POST"])
def generate_qr():
    try:
        data = request.get_json()

        # Handle destination (URL to encode in QR)
        raw_dest = data.get('destination', 'https://qrforus.com')
        destination = raw_dest[0] if isinstance(raw_dest, list) else raw_dest or "https://qrforus.com"

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(destination)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # Save image to buffer
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        # Convert to base64 for email attachment
        encoded_image = base64.b64encode(buffer.read()).decode()

        # Email content
        recipient_email = data.get("email", "")
        user_message = data.get("message", "")
        full_message = f"""QR for US (TM)

Thank you for using QR for US (TM) - your customized, personal QR code is attached and ready to use.

Destination: {destination}

To use it:
- Click or tap the QR image to test it
- Copy and paste into your project
- Or print it (PNG is high-res and printable)

Your Message:
{user_message}

Need a do-over? You can regenerate your code up to 2 times in the next 24 hours at no charge using the custom link sent with your order.

Thanks again for using QR for US (TM)!

- The QR for US Team"""

        # Send email via Mailgun
        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            data={
                "from": FROM_EMAIL,
                "to": [recipient_email],
                "subject": "Your QR for US (TM) Code is Ready",
                "text": full_message,
            },
            files={"attachment": ("qr_code.png", base64.b64decode(encoded_image))}
        )

        if response.status_code == 200:
            return jsonify({"message": "QR code generated and email sent successfully."}), 200
        else:
            return jsonify({"error": "Failed to send email", "details": response.text}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500