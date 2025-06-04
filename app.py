
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer, SquareModuleDrawer
from PIL import Image, ImageColor
import io
import os
import base64
import requests
import logging

app = Flask(__name__)
CORS(app)

MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
SENDER_EMAIL = f"QR for US <qrforus@{MAILGUN_DOMAIN}>"

@app.route("/")
def index():
    return "QR for US backend is running."

@app.route("/generate_qr", methods=["POST"])
def generate_qr():
    try:
        data = request.json
        logging.info("✅ Using NEW QR generation method")

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data["url"])
        qr.make(fit=True)

        fill_color = data.get("fill_color", "#000000")
        back_color = data.get("back_color", "#FFFFFF")

        try:
            fill_rgb = ImageColor.getrgb(fill_color)
            back_rgb = ImageColor.getrgb(back_color)
        except ValueError:
            logging.error("Invalid color format")
            return jsonify({"error": "Invalid color format"}), 400

        shape = data.get("shape", "square")
        drawer = RoundedModuleDrawer() if shape == "rounded" else SquareModuleDrawer()

        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=drawer,
            fill_color=fill_rgb,
            back_color=back_rgb
        )

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        # Send via Mailgun
        recipient_email = data.get("email")
        if MAILGUN_DOMAIN and MAILGUN_API_KEY and recipient_email:
            response = requests.post(
                f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
                auth=("api", MAILGUN_API_KEY),
                files={"attachment": ("qr_code.png", buffer.getvalue())},
                data={
                    "from": SENDER_EMAIL,
                    "to": recipient_email,
                    "subject": "🎉 Your QR Code from QR for US",
                    "html": (
                        "<p>Hello {name},</p>"
                        "<p>Thanks for using QR for US!</p>"
                        "<p>Your personalized QR code is attached.</p>"
                        "<p><strong>Need to do it over?</strong> You can regenerate it up to 2 times in 24 hours.</p>"
                        "<p>🔗 <a href='https://qrforus.com/doover'>Do Over Link</a></p>"
                        "<p>– The QR for US Team</p>"
                    ).format(name=data.get("first_name", ""))
                }
            )
            logging.info(f"📧 Mailgun response: {response.status_code} – {response.text}")

        return send_file(
            io.BytesIO(buffer.getvalue()),
            mimetype='image/png',
            as_attachment=True,
            download_name='qr_code.png'
        )

    except Exception as e:
        logging.exception("🔥 QR generation or email delivery failed")
        return jsonify({"error": str(e)}), 500
