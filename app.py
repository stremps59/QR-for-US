
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

    # Extract required fields
    name = data.get("name", "Customer")
    email = data.get("email")
    destination = data.get("destination")
    qr_type = data.get("qr_type", "standard")
    color = data.get("color", "black")

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

    # Convert image to base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode("utf-8")

    # Generate Do Over link
    qr_id = str(uuid.uuid4())[:8]
    do_over_link = f"https://qrforus.com/do-over?id={qr_id}"

    # Prepare email via Mailgun
    MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
    MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")

    if not MAILGUN_API_KEY or not MAILGUN_DOMAIN:
        return jsonify({"error": "Missing Mailgun credentials"}), 500

    mailgun_url = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"

    response = requests.post(
        mailgun_url,
        auth=("api", MAILGUN_API_KEY),
        files=[("attachment", ("qr_code.png", img_bytes))],
        data={
            "from": f"QR for US <mailgun@{MAILGUN_DOMAIN}>",
            "to": email,
            "subject": "Your QR Code is Ready!",
            "html": f"""
<html>
<body>
    <p>Hi {name},</p>
    <p>Here's your custom QR code. You can scan it or click it below:</p>
    <p><img src="data:image/png;base64,{img_base64}" alt="QR Code" /></p>
    <p><a href="{destination}">Go to your link</a></p>
    <p><a href="{do_over_link}">Need a do-over?</a></p>
</body>
</html>
"""
        }
    )

    if response.status_code != 200:
        return jsonify({"error": "Failed to send email", "details": response.text}), 500

    return jsonify({
        "message": "QR created and email sent",
        "do_over_link": do_over_link
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
