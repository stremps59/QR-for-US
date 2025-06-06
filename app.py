
import os
import io
import uuid
import base64
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import qrcode_styled as qrcode
from qrcode_styled.image.styles.moduledrawers import SquareModuleDrawer, GappedSquareModuleDrawer, CircleModuleDrawer
from qrcode_styled.image.styles.colormasks import SolidFillColorMask
from qrcode_styled.image.styles.eyedrawers import SquareEyeDrawer, CircleEyeDrawer, RoundedEyeDrawer

app = Flask(__name__)
CORS(app)

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

        def get_field(label):
            for field in fields:
                if field.get("label") == label:
                    return field.get("value")
            return ""

        to_email = get_field("Your Email")
        destination_url = get_field("Destination URL")
        qr_type = get_field("Type")
        border_style = get_field("Border Style")
        corner_style = get_field("Corner Style")
        color_primary = get_field("Primary Color")
        color_secondary = get_field("Secondary Color")
        image_url = get_field("Upload Image")

        def normalize(value):
            if isinstance(value, list):
                return value[0].lower()
            elif isinstance(value, str):
                return value.lower()
            return ""

        border_style = normalize(border_style)
        corner_style = normalize(corner_style)

        drawer_lookup = {
            "square": SquareModuleDrawer(),
            "dot": CircleModuleDrawer(),
            "frame": GappedSquareModuleDrawer()
        }
        eye_drawer_lookup = {
            "square": SquareEyeDrawer(),
            "circle": CircleEyeDrawer(),
            "rounded": RoundedEyeDrawer(),
            "framed": SquareEyeDrawer()
        }

        drawer = drawer_lookup.get(border_style, SquareModuleDrawer())
        eye_drawer = eye_drawer_lookup.get(corner_style, SquareEyeDrawer())

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(destination_url)
        qr.make(fit=True)

        img = qr.make_image(
            image_factory=qrcode.image.styledpil.StyledPilImage,
            module_drawer=drawer,
            eye_drawer=eye_drawer,
            color_mask=SolidFillColorMask(back_color="white", front_color=color_primary or "black")
        )

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        img_bytes = buffer.read()
        encoded_img = base64.b64encode(img_bytes).decode()

        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            files=[("attachment", ("qr_code.png", img_bytes))],
            data={
                "from": MAILGUN_FROM,
                "to": to_email,
                "subject": "Your QR Code from QR for US",
                "html": f"<html><body><p>Thanks for using QR for US!</p><p>Click or scan your attached QR code to visit:<br><strong>{destination_url}</strong></p></body></html>"
            },
        )

        return jsonify({"status": "success", "mailgun_status": response.status_code}), 200

    except Exception as e:
        sys.stderr.write(f"[QR-ERROR] {e}\n")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(debug=False, host="0.0.0.0", port=port)
