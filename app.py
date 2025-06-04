
from flask import Flask, request, jsonify
import qrcode
import io
import base64
import os
import uuid
import requests
import traceback
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

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
        destination = fields.get("where should your qr code point (website/url)")
        qr_type = fields.get("what type of qr would you like?", ["standard"])
        if isinstance(qr_type, list):
            qr_type = qr_type[0]
        color = fields.get("data modules color (hex# or named color)", "black")

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(destination or "https://qrforus.com")
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
            try:
                html_body = f"""<html>
<body>
<p>Hi {name},</p>
<p>Your QR for US™ QR code is ready to use!</p>
<p><img src="data:image/png;base64,{img_str}" alt="QR Code" /></p>
<p>This code is your bridge between digital life and real-life moments. Here’s how to use it:</p>
<ul>
  <li><strong>Scan it:</strong> Use your phone’s camera or a QR scanner to instantly visit your link.</li>
  <li><strong>Click it:</strong> If viewing this email on your device, click the QR code above to open the destination.</li>
  <li><strong>Save it:</strong> Right-click (or tap & hold) on the image to save it for printing, posting, or sharing.</li>
</ul>
<p><a href="{do_over_link}">Need to make a quick change? Use your one-time Do Over link.</a></p>
<p><em>No account required. No subscriptions. Just your story — beautifully connected.</em></p>
<p>— QR for US™</p>
</body>
</html>
"""

                response = requests.post(
                    f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
                    auth=("api", MAILGUN_API_KEY),
                    data={
                        "from": FROM_EMAIL,
                        "to": email,
                        "subject": "Your QR for US™ QR code is ready to use!",
                        "html": html_body
                    }
                )
                print("📤 Mailgun response:", response.status_code, response.text)
            except Exception:
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
