
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
        print("📦 Raw incoming data:", data)

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
            print("❌ Invalid color format")
            return jsonify({"error": "Invalid color format"}), 400

        shape = data.get("shape", "square")
        drawer = RoundedModuleDrawer() if shape == "rounded" else SquareModuleDrawer()

        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=drawer,
            fill_color=fill_rgb,
            back_color=back_rgb
        )

        if data.get("center_image"):
            logo_path = "center_image.png"
            with open(logo_path, "wb") as f:
                f.write(base64.b64decode(data["center_image"]))
            logo = Image.open(logo_path)
            img = img.convert("RGB")
            pos = ((img.size[0] - logo.size[0]) // 2, (img.size[1] - logo.size[1]) // 2)
            img.paste(logo, pos, mask=logo if logo.mode == 'RGBA' else None)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        recipient = data["email"]
        subject = "Your QR Code from QR for US"
        body = (
            f"Hi!\n\nHere's your QR code linking to: {data['url']}\n"
            "You can scan or click the attached image to go directly to your destination.\n\n"
            "Thanks for using QR for US!"
        )

        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            files={"attachment": ("qr_code.png", buffer.getvalue())},
            data={
                "from": SENDER_EMAIL,
                "to": recipient,
                "subject": subject,
                "text": body
            },
        )

        print("📧 Mailgun response:", response.status_code, response.text)

        if response.status_code == 200:
            return jsonify({"status": "success"})
        else:
            return jsonify({"error": "Email failed", "details": response.text}), 500

    except Exception as e:
        print("🔥 Error during QR generation:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
