
from flask import Flask, request, jsonify
import qrcode
import io
import base64
import os
import uuid
import requests
import traceback
from flask_cors import CORS
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import SquareModuleDrawer, GappedSquareModuleDrawer, CircleModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from PIL import ImageColor

app = Flask(__name__)
CORS(app)

def validate_color(color_str, default="black"):
    try:
        ImageColor.getrgb(color_str)
        return color_str
    except Exception:
        return default

@app.route("/", methods=["GET"])
def home():
    return "QR for US is running!"

@app.route("/generate_qr", methods=["POST"])
def generate_qr():
    try:
        data = request.get_json()
        print("📦 Raw incoming data:", data)

        fields = {field['label'].strip().lower(): field['value'] for field in data.get("data", {}).get("fields", [])}

        name = fields.get("first name", "QR User")
        email = fields.get("email address")
        destination = fields.get("where should your qr code point (website/url)", "https://qrforus.com")
        qr_type = fields.get("what type of qr would you like?", ["standard"])[0] if isinstance(fields.get("what type of qr would you like?"), list) else "standard"
        color_raw = fields.get("data modules color (hex# or named color)", "black")
        shape = fields.get("what border style would you like?", ["square"])[0] if isinstance(fields.get("what border style would you like?"), list) else "square"

        color = validate_color(color_raw)
        logo = None  # Placeholder for future use

        print(f"🧾 Parsed - name: {name}, email: {email}, destination: {destination}, color: {color}, shape: {shape}")

        shape_map = {
            "square": SquareModuleDrawer(),
            "gapped": GappedSquareModuleDrawer(),
            "circle": CircleModuleDrawer()
        }

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(destination)
        qr.make(fit=True)

        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=shape_map.get(shape, SquareModuleDrawer()),
            color_mask=SolidFillColorMask(back_color="white", front_color=color)
        ).convert("RGB")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

        qr_id = str(uuid.uuid4())[:8]
        do_over_link = f"https://qrforus.com/do-over?id={qr_id}"

        MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
        MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
        FROM_EMAIL = os.getenv("FROM_EMAIL")

        print(f"🔐 ENV - API Key Present: {bool(MAILGUN_API_KEY)}, Domain: {MAILGUN_DOMAIN}, From: {FROM_EMAIL}, To: {email}")

        if MAILGUN_API_KEY and MAILGUN_DOMAIN and FROM_EMAIL and email:
            try:
                html_body = (
                    f"<p>Hi {name},</p>"
                    f"<p>Your QR Code is ready:</p>"
                    f"<p><img src='data:image/png;base64,{img_str}' alt='QR Code' /></p>"
                    f"<p><a href='{do_over_link}'>Click here to Do Over</a></p>"
                    f"<p>Thanks for using <strong>QR for US</strong> — your simple way to tell a story or share a link through a personalized code.</p>"
                )
                print("📧 Email HTML:", html_body)

                response = requests.post(
                    f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
                    auth=("api", MAILGUN_API_KEY),
                    data={
                        "from": FROM_EMAIL,
                        "to": email,
                        "subject": "Your QR Code is Ready",
                        "html": html_body
                    }
                )
                print("📤 Mailgun response:", response.status_code, response.text)
            except Exception as e:
                print("❌ Exception while sending email:")
                traceback.print_exc()

        return jsonify({
            "message": "QR created",
            "clickable_image": f"data:image/png;base64,{img_str}",
            "do_over_link": do_over_link
        })

    except Exception as err:
        print("🔥 Top-level error caught:")
        traceback.print_exc()
        return jsonify({"error": str(err)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
