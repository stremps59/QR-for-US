from flask import Flask, request, jsonify
from flask_cors import CORS
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import (
    RoundedModuleDrawer, SquareModuleDrawer, CircleModuleDrawer
)
from qrcode.image.styles.eyedrawers import (
    SquareEyeDrawer, RoundedEyeDrawer, HorizontalBarsEyeDrawer
)
from PIL import Image
import io
import base64
import requests
import os
import re

app = Flask(__name__)
CORS(app)

MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
FROM_EMAIL = os.getenv("FROM_EMAIL")

def is_valid_color(color_value):
    named_colors = {
        "black", "white", "red", "blue", "green", "yellow", "purple", "orange",
        "gray", "grey", "cyan", "magenta", "pink", "brown", "lime", "navy",
        "teal", "aqua", "maroon", "olive", "silver"
    }
    hex_pattern = r"^#?[0-9a-fA-F]{6}$"
    return bool(re.match(hex_pattern, color_value.lstrip("#"))) or color_value.lower() in named_colors

@app.route("/generate_qr", methods=["POST"])
def generate_qr():
    data = request.get_json()
    app.logger.info(f"Raw form submission received: {data}")

    form = {
        "email": data.get("Email address", ""),
        "url": data.get("Where should your QR Code point (Website/URL)?", ""),
        "fill_color": data.get("Data modules color (HEX# or Named color)", "black"),
        "eye_color": data.get("Corner finder dots color (HEX# or Named color)", "black"),
        "border_color": data.get("Border Color (HEX# or Named color)", "black"),
        "center_color": data.get("Center image color (if no image uploaded; HEX# or Named color)", "white"),
        "border_style": data.get("Border Style?", "square"),
        "eye_style": data.get("Corner Finder Pattern Style?", "square"),
        "discount_code": data.get("Discount code", ""),
        "first_name": data.get("First Name", ""),
        "last_name": data.get("Last Name", ""),
        "image_data": data.get("Upload a center image (optional)", "")
    }

    if not form["url"] or not form["email"]:
        return jsonify({"error": "URL and Email are required fields."}), 400

    for key in ["fill_color", "eye_color", "border_color", "center_color"]:
        if not is_valid_color(form[key]):
            return jsonify({"error": f"Invalid color value provided for {key.replace('_', ' ')}."}), 400

    module_styles = {
        "square": SquareModuleDrawer(),
        "rounded": RoundedModuleDrawer(),
        "circle": CircleModuleDrawer(),
    }
    eye_styles = {
        "square": SquareEyeDrawer(),
        "rounded": RoundedEyeDrawer(),
        "horizontal": HorizontalBarsEyeDrawer(),
    }

    module_drawer = module_styles.get(form["border_style"].lower(), SquareModuleDrawer())
    eye_drawer = eye_styles.get(form["eye_style"].lower(), SquareEyeDrawer())

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(form["url"])
    qr.make(fit=True)

    center_img = None
    if form["image_data"]:
        try:
            header, encoded = form["image_data"].split(",", 1)
            decoded = base64.b64decode(encoded)
            center_img = Image.open(io.BytesIO(decoded))
        except (ValueError, Exception) as e:
            app.logger.warning(f"Image decode failed: {e}")
            return jsonify({"error": "Failed to decode the uploaded image."}), 400

    try:
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=module_drawer,
            eye_drawer=eye_drawer,
            color_mask=None,
            embeded_image=center_img,
            fill_color=form["fill_color"],
            back_color=form["center_color"]
        )
    except Exception as e:
        app.logger.error(f"QR generation error: {e}")
        return jsonify({"error": "Failed to generate QR code image."}), 500

    with io.BytesIO() as img_byte_arr:
        img.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)

        if MAILGUN_API_KEY and MAILGUN_DOMAIN and FROM_EMAIL:
            try:
                response = requests.post(
                    f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
                    auth=("api", MAILGUN_API_KEY),
                    files=[("attachment", ("qr_code.png", img_byte_arr.getvalue()))],
                    data={
                        "from": FROM_EMAIL,
                        "to": [form["email"]],
                        "subject": "Your QR Code from QR for US",
                        "text": f"Hi {form['first_name']},\n\nYour QR code is attached. It points to: {form['url']}"
                    },
                )
                response.raise_for_status()
                return jsonify({"message": "QR code sent successfully"}), 200
            except requests.exceptions.RequestException as e:
                app.logger.error(f"Error sending email: {e}")
                return jsonify({"error": "Failed to send email"}), 500
        else:
            app.logger.error("Mailgun API key, domain, or from email not set.")
            return jsonify({"error": "Failed to send email due to missing configuration."}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
