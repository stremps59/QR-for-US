
from flask import Flask, request, jsonify
import qrcode
import io
import base64
import os
import uuid
import requests
from flask_cors import CORS
from PIL import Image
from io import BytesIO

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def home():
    return "QR for US is running!"

@app.route("/generate_qr", methods=["POST"])
def generate_qr():
    data = request.get_json()

    # Extract required fields
    name = data.get("name")
    email = data.get("email")
    destination = data.get("destination")
    qr_type = data.get("qr_type", "standard")
    color = data.get("color", "black")
    shape = data.get("shape", "square")
    logo = data.get("logo", None)

    # Generate QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(destination)
    qr.make(fit=True)

    img = qr.make_image(fill_color=color, back_color="white").convert("RGB")

    # Optional logo handling
    if logo:
        try:
            logo_response = requests.get(logo)
            logo_img = Image.open(BytesIO(logo_response.content))

            # Resize logo to fit inside QR code
            basewidth = int(img.size[0] / 4)
            wpercent = basewidth / float(logo_img.size[0])
            hsize = int(float(logo_img.size[1]) * wpercent)
            logo_img = logo_img.resize((basewidth, hsize), Image.ANTIALIAS)

            # Paste logo into QR code
            pos = (
                (img.size[0] - logo_img.size[0]) // 2,
                (img.size[1] - logo_img.size[1]) // 2
            )
            img.paste(logo_img, pos)

        except Exception as e:
            print(f"Logo insert failed: {e}")

    # Convert to base64 for clickable delivery
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # Simulate Do Over link generation
    qr_id = str(uuid.uuid4())[:8]
    do_over_link = f"https://qrforus.com/do-over?id={qr_id}"

    return jsonify({
        "message": "QR created",
        "clickable_image": f"data:image/png;base64,{img_str}",
        "do_over_link": do_over_link
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
