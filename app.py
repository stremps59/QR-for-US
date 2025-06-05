
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
import io
import requests
from PIL import Image
import base64
import os

app = Flask(__name__)
CORS(app)

MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
FROM_EMAIL = os.getenv("FROM_EMAIL")

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    data = request.get_json()

    # Extract form data
    form = {
        "email": data.get("Email address"),
        "url": data.get("Where should your QR Code point (Website/URL)?"),
        "fill_color": data.get("Data modules color (HEX# or Named color)"),
        "eye_color": data.get("Corner finder dots color (HEX# or Named color)"),
        "border_color": data.get("Border Color (HEX# or Named color)"),
        "center_color": data.get("Center image color (if no image uploaded; HEX# or Named color)"),
        "border_style": data.get("Border Style?"),
        "eye_style": data.get("Corner Finder Pattern Style?"),
        "discount_code": data.get("Discount code"),
        "first_name": data.get("First Name"),
        "last_name": data.get("Last Name"),
    }

    destination_url = form["url"]
    fill_color = form["fill_color"] or "black"

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(destination_url)
    qr.make(fit=True)

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        fill_color=fill_color,
        back_color="white"
    )

    # Save to a BytesIO object
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)

    # Send email via Mailgun
    requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        files=[("attachment", ("qr_code.png", img_byte_arr.read()))],
        data={
            "from": FROM_EMAIL,
            "to": [form["email"]],
            "subject": "Your QR Code from QR for US",
            "text": f"Hi {form['first_name']},\n\nYour QR code is attached. It points to: {destination_url}"
        },
    )

    return jsonify({"message": "QR code sent successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
