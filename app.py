
import os
import io
import qrcode
import requests
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import SquareModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
import base64
import logging

app = Flask(__name__)
CORS(app)

MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
FROM_EMAIL = "QR for US <qrforus@" + MAILGUN_DOMAIN + ">"

logging.basicConfig(level=logging.INFO)

@app.route("/")
def home():
    return "QR Generator is Live!"

@app.route("/generate_qr", methods=["POST"])
def generate_qr():
    try:
        data = request.get_json()
        target_url = data.get("target_url", "https://qrforus.com")
        recipient_email = data.get("email", "test@example.com")
        fill_color = data.get("fill_color", "#000000")
        back_color = data.get("back_color", "#ffffff")

        logging.info(f"Generating QR for {recipient_email} to {target_url}")

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(target_url)
        qr.make(fit=True)

        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=SquareModuleDrawer(),
            color_mask=SolidFillColorMask(back_color=back_color, front_color=fill_color)
        )

        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        buffered.seek(0)
        encoded_image = base64.b64encode(buffered.read()).decode()

        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            files=[("attachment", ("qr_code.png", buffered.getvalue()))],
            data={
                "from": FROM_EMAIL,
                "to": recipient_email,
                "subject": "Your Custom QR Code is Ready!",
                "html": f"<html><body><p>Hi there! 👋</p><p>Here’s your personalized QR code:</p><img src='cid:qr_code.png'><p>It links to: <a href='{target_url}'>{target_url}</a></p><p>Thanks for using QR for US™.</p></body></html>"
            }
        )

        if response.status_code == 200:
            logging.info("Email sent successfully.")
        else:
            logging.error(f"Email failed: {response.text}")

        return jsonify({"message": "QR code generated and email sent."})

    except Exception as e:
        logging.exception("Error during QR code generation or email sending.")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
