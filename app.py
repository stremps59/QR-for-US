
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
    print("🔔 /generate_qr endpoint hit", flush=True)

    data = request.get_json()
    print(f"📦 Raw incoming data: {data}", flush=True)

    # Extract fields
    name = data.get("name")
    email = data.get("email")
    destination = data.get("destination")
    qr_type = data.get("qr_type", "standard")
    color = data.get("color", "black")
    shape = data.get("shape", "square")
    logo = data.get("logo", None)

    print(f"🧾 Parsed - name: {name}, email: {email}, destination: {destination}", flush=True)

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

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

    qr_id = str(uuid.uuid4())[:8]
    do_over_link = f"https://qrforus.com/do-over?id={qr_id}"

    # Email setup
    MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
    MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
    FROM_EMAIL = os.getenv("FROM_EMAIL")

    print(f"🔐 ENV - API Key Present: {bool(MAILGUN_API_KEY)}, Domain: {MAILGUN_DOMAIN}, From: {FROM_EMAIL}", flush=True)

    if MAILGUN_API_KEY and MAILGUN_DOMAIN and FROM_EMAIL:
        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            data={
                "from": FROM_EMAIL,
                "to": email,
                "subject": "Your QR Code is Ready",
                "html": f"<p>Hi {name},</p><p>Your QR Code is ready:</p><img src='data:image/png;base64,{img_str}' /><p><a href='{do_over_link}'>Click here to Do Over</a></p>"
            }
        )
        print(f"📤 Mailgun response: {response.status_code} {response.text}", flush=True)
    else:
        print("🚨 Missing Mailgun ENV vars; skipping email send", flush=True)

    return jsonify({
        "message": "QR created",
        "clickable_image": f"data:image/png;base64,{img_str}",
        "do_over_link": do_over_link
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
