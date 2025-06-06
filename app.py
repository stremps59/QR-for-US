
import os
import io
import uuid
import base64
import qrcode as qrcode
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

# Advanced styling modules
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import SquareModuleDrawer, RoundedModuleDrawer, CircleModuleDrawer
from qrcode.image.styles.eyedrawers import SquareEyeDrawer, RoundedEyeDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask

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
        data = request.get_json(force=True) or {}
        fields = data.get("data", {}).get("fields", [])

        def get_field(label, default=""):
            for field in fields:
                if isinstance(field, dict) and field.get("label", "").strip().lower() == label.strip().lower():
                    return field.get("value", default)
            return default

        first_name = get_field("First Name", "")
        email = get_field("Email address", "")
        destination = get_field("Where should your QR Code point (Website/URL)?", "https://qrforus.com")
        border_style = get_field("Border Style?", "Square").lower()
        corner_style = get_field("Corner Finder Pattern Style?", "Standard").lower()
        border_color = get_field("Border Color (HEX# or Named color)", "black")
        dot_color = get_field("Corner finder dots color (HEX# or Named color)", "black")
        center_color = get_field("Center image color (if no image uploaded; HEX# or Named color)", "black")
        data_color = get_field("Data modules color (HEX# or Named color)", "black")

        print(f"Color Fields => Data: {data_color}, Border: {border_color}, Dots: {dot_color}, Center: {center_color}")
        print(f"Style Fields => Border: {border_style}, Eye: {corner_style}")

        module_drawer = {
            "square": SquareModuleDrawer(),
            "rounded": RoundedModuleDrawer(),
            "circle": CircleModuleDrawer()
        }.get(border_style, SquareModuleDrawer())

        eye_drawer = {
            "standard": SquareEyeDrawer(),
            "rounded": RoundedEyeDrawer(),
        }.get(corner_style, SquareEyeDrawer())

        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
        qr.add_data(destination)
        qr.make(fit=True)

        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=module_drawer,
            eye_drawer=eye_drawer,
            color_mask=SolidFillColorMask(back_color="white", front_color=data_color)
        ).convert("RGB")

        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        html_body = (
            f"<p>Hi {first_name},</p>"
            f"<p>Your QR Code is ready!</p>"
            f"<p>It's attached to this email as a PNG image -- ready to use in print, online, and everywhere in between.</p>"
            f"<p>QR for US™ connects your stories, profiles, and passions to the world -- one QR at a time.</p>"
        )

        return jsonify({"qr_base64": img_base64, "email_body": html_body})

    except Exception as e:
        import sys
        sys.stderr.write(f"[QR-ERROR] {e}\n")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
