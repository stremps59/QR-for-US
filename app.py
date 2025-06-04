
import os
import io
import base64
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer, GappedSquareModuleDrawer, SquareModuleDrawer
from qrcode.image.styles.colordrawers import SolidFillColorMask
from PIL import Image
import requests

app = Flask(__name__)
CORS(app)

MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
MAILGUN_FROM = os.getenv("MAILGUN_FROM", "QR for US <mailgun@{}>".format(MAILGUN_DOMAIN))

def generate_qr_image(data, fill_color="black", back_color="white", image_format="PNG", center_image=None, shape="square"):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)

    if shape == "rounded":
        drawer = RoundedModuleDrawer()
    elif shape == "gapped":
        drawer = GappedSquareModuleDrawer()
    else:
        drawer = SquareModuleDrawer()

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=drawer,
        color_mask=SolidFillColorMask(back_color=back_color, front_color=fill_color)
    )

    if center_image:
        try:
            logo = Image.open(io.BytesIO(base64.b64decode(center_image)))
            logo = logo.convert("RGBA")
            box = (
                (img.size[0] - logo.size[0]) // 2,
                (img.size[1] - logo.size[1]) // 2,
            )
            img.paste(logo, box, logo)
        except Exception as e:
            print(f"⚠️ Error adding center image: {e}")

    output = io.BytesIO()
    img.save(output, format=image_format)
    output.seek(0)
    return output

@app.route("/generate_qr", methods=["POST"])
def generate_qr():
    try:
        content = request.json
        data = content.get("data")
        email = content.get("email")
        fill_color = content.get("fill_color", "black")
        back_color = content.get("back_color", "white")
        shape = content.get("shape", "square")
        center_image = content.get("center_image")

        print("📥 Received request to generate QR code")
        img_stream = generate_qr_image(data, fill_color, back_color, "PNG", center_image, shape)

        if email:
            print("📨 Preparing to send email via Mailgun...")
            response = requests.post(
                f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
                auth=("api", MAILGUN_API_KEY),
                files={"attachment": ("qr.png", img_stream, "image/png")},
                data={
                    "from": MAILGUN_FROM,
                    "to": email,
                    "subject": "Your QR code is ready",
                    "text": "Thanks for using QR for US™! Your QR code is attached and ready to use."
                },
            )
            print(f"✅ Mailgun response: {response.status_code}, {response.text}")

        img_stream.seek(0)
        return send_file(img_stream, mimetype="image/png")

    except Exception as e:
        print(f"🔥 Error generating or sending QR: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
