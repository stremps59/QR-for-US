
from flask import Flask, request, jsonify
import qrcode
import io
import base64
import os
import uuid
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def home():
    return "QR for US is running!"

@app.route("/generate_qr", methods=["POST"])
def generate_qr():
    data = request.get_json()
    fields = data.get("data", {}).get("fields", [])

    def get_field(label):
        for field in fields:
            if field.get("label") == label:
                return field.get("value")
        return None

    name = get_field("First Name")
    email = get_field("Email address")
    destination = get_field("Where should your QR Code point (Website/URL)")

    qr_type = get_field("What type of QR would you like?") or "standard"
    color = get_field("Data modules color (HEX# or Named color)") or "black"
    shape = get_field("What border style would you like?") or "square"
    logo = None  # Optional logo handling can be added later

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(destination)
    qr.make(fit=True)

    img = qr.make_image(fill_color=color, back_color="white").convert("RGB")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

    qr_id = str(uuid.uuid4())[:8]
    do_over_link = f"https://qrforus.com/do-over?id={qr_id}"

    MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
    MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
    FROM_EMAIL = os.getenv("FROM_EMAIL")

    if MAILGUN_API_KEY and MAILGUN_DOMAIN and FROM_EMAIL and email:
        requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            data={
                "from": FROM_EMAIL,
                "to": email,
                "subject": "Your QR Code is Ready",
                "html": f"<p>Hi {name},</p><p>Your QR Code is ready:</p><img src='data:image/png;base64,{img_str}' /><p><a href='{do_over_link}'>Click here to Do Over</a></p>"
            }
        )

    return jsonify({
        "message": "QR created",
        "clickable_image": f"data:image/png;base64,{img_str}",
        "do_over_link": do_over_link
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
