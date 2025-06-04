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
        else:
            qr_type = "standard"
        color = (fields.get("data modules color (hex# or named color)", "black") or "black").strip()
        shape = fields.get("what border style would you like?", ["square"])
        if isinstance(shape, list):
            shape = shape[0]
        else:
            shape = "square"

        print(f"🧾 Parsed - name: {name}, email: {email}, destination: {destination}")

        # Generate QR code
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
        buffer.seek(0)

        qr_id = str(uuid.uuid4())[:8]
        do_over_link = f"https://qrforus.com/do-over?id={qr_id}"

        MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
        MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
        FROM_EMAIL = os.getenv("FROM_EMAIL")

        print(f"🔐 ENV - API Key Present: {bool(MAILGUN_API_KEY)}, Domain: {MAILGUN_DOMAIN}, From: {FROM_EMAIL}, To: {email}")

        if MAILGUN_API_KEY and MAILGUN_DOMAIN and FROM_EMAIL and email:
            try:
                html_body = f"""<p>Hi {name},</p>
<p>Your custom QR for US™ code is ready to use.</p>
<p>This one QR can be scanned, clicked, saved, or shared — on phones, flyers, websites, business cards, and anywhere else people connect with your story.</p>
<p><strong>How to use your QR:</strong></p>
<ul>
  <li><strong>Scan:</strong> Open any camera app and point it at the code.</li>
  <li><strong>Click:</strong> If viewing this email on a device, just tap the code image.</li>
  <li><strong>Save:</strong> Right-click (or tap+hold on mobile) to download the image as a PNG.</li>
</ul>
<p><a href="{do_over_link}">Need to make a change? Use our “Do Over” feature here.</a></p>
<p>Thanks for using QR for US™ — we connect real-life moments to the digital world.</p>
<p>—<br>QR for US™<br><a href="https://qrforus.com">https://qrforus.com</a></p>
"""

                response = requests.post(
                    f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
                    auth=("api", MAILGUN_API_KEY),
                    files=[("attachment", ("qr_code.png", buffer.getvalue(), "image/png"))],
                    data={
                        "from": FROM_EMAIL,
                        "to": email,
                        "subject": "Your QR for US™ code is ready to use!",
                        "html": html_body
                    }
                )
                print("📤 Mailgun response:", response.status_code, response.text)
            except Exception as e:
                print("❌ Exception while sending email:")
                traceback.print_exc()

        return jsonify({
            "message": "QR created",
            "do_over_link": do_over_link
        })

    except Exception as err:
        print("🔥 Top-level error caught:")
        traceback.print_exc()
        return jsonify({"error": str(err)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)