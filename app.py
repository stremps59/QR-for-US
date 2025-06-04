
import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer, CircleModuleDrawer, SquareModuleDrawer
from qrcode.image.styles.eye import RoundedEyeDrawer, SquareEyeDrawer, HorizontalBarsEyeDrawer
from PIL import Image, ImageColor
from io import BytesIO
import base64
import logging

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

def parse_color(value, fallback):
    try:
        return ImageColor.getrgb(value)
    except:
        return ImageColor.getrgb(fallback)

@app.route("/generate_qr", methods=["POST"])
def generate_qr():
    try:
        data = request.get_json()
        logging.info(f"Raw incoming data: {data}")
        fields = data.get("data", {}).get("fields", [])

        def get_field(label, default=""):
            for f in fields:
                if f.get("label", "").strip().lower() == label.strip().lower():
                    return f.get("value", default)
            return default

        recipient = get_field("Email address")
        destination = get_field("Where should your QR Code point (Website/URL)?", "https://qrforus.com").strip()

        border_color = parse_color(get_field("Border Color (HEX# or Named color)", "black"), "black")
        finder_color = parse_color(get_field("Corner finder dots color (HEX# or Named color)", "black"), "black")
        center_color = parse_color(get_field("Center image color (if no image uploaded; HEX# or Named color)", "black"), "black")
        data_color = parse_color(get_field("Data modules color (HEX# or Named color)", "black"), "black")

        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
        qr.add_data(destination)
        qr.make(fit=True)

        img = qr.make_image(
            image_factory=StyledPilImage,
            color_mask=SolidFillColorMask(
                back_color="white",
                front_color=data_color,
                center_color=center_color,
                top_left_color=finder_color,
                top_right_color=finder_color,
                bottom_left_color=finder_color
            ),
            module_drawer=SquareModuleDrawer(),
            eye_drawer=SquareEyeDrawer()
        )

        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()
        encoded_img = base64.b64encode(img_bytes).decode("utf-8")

        mailgun_domain = os.getenv("MAILGUN_DOMAIN")
        mailgun_api_key = os.getenv("MAILGUN_API_KEY")

        if not mailgun_domain or not mailgun_api_key:
            raise Exception("Missing Mailgun environment variables")

        mailgun_url = f"https://api.mailgun.net/v3/{mailgun_domain}/messages"

        response = requests.post(
            mailgun_url,
            auth=("api", mailgun_api_key),
            files=[("attachment", ("qr.png", img_bytes, "image/png"))],
            data={
                "from": f"QR for US <mailgun@{mailgun_domain}>",
                "to": recipient,
                "subject": "Your QR for US™ code is ready to use!",
                "html": (
                    f"<p>Hi {get_field('First Name', 'there')},</p>"
                    f"<p>Your custom QR for US™ code is <strong>ready to use</strong>.</p>"
                    f"<img src='cid:qr.png' alt='Your QR Code' style='width:200px;height:200px;' />"
                    f"<p>This one QR can be scanned, clicked, saved, or shared — on phones, flyers, websites, "
                    f"business cards, and anywhere else people connect with your story.</p>"
                    f"<p>Thanks for using QR for US™ — we connect real-life moments to the digital world.</p>"
                    f"<p>Scan It. Click It. Share your story.<br><a href='https://qrforus.com'>https://qrforus.com</a></p>"
                )
            }
        )

        logging.info(f"📤 Mailgun response: {response.status_code} {response.text}")
        return jsonify({"success": True, "email_response": response.text})

    except Exception as e:
        logging.error("Error during QR code generation or email sending.", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=10000)
