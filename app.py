
import os
import requests
import qrcode
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
from io import BytesIO
import base64

app = Flask(__name__)
CORS(app)

MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN')
FROM_EMAIL = os.getenv('FROM_EMAIL')
TO_EMAIL = os.getenv('TO_EMAIL') or "stremps@sbcglobal.net"

@app.route('/')
def index():
    return "App running..."

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    try:
        data = request.get_json()
        fields = data.get('data', {}).get('fields', [])

        destination = next(
            (f['value'] for f in fields if isinstance(f, dict) and f.get('label') == "Where should your QR Code point (Website/URL)?"),
            ''
        ).strip() or "https://qrforus.com"

        qr = qrcode.make(destination)
        buffered = BytesIO()
        qr.save(buffered, format="PNG")
        img_data = buffered.getvalue()
        img_base64 = base64.b64encode(img_data).decode()

        # Send the email with full HTML
        html = f"""
        <p>Hi Scott,</p>
        <p>Your custom QR for US™ code is <strong>ready to use</strong>.</p>
        <p><img src="cid:qr_code.png" alt="QR Code"></p>
        <p>This one QR can be scanned, clicked, saved, or shared — on phones, flyers, websites, business cards, and anywhere else people connect with your story.</p>
        <h4>How to use your QR:</h4>
        <ul>
            <li><strong>Scan:</strong> Open any camera app and point it at the code.</li>
            <li><strong>Click:</strong> If viewing this email on a device, just tap the code image.</li>
            <li><strong>Save:</strong> Right-click (or tap+hold on mobile) to download the image as a PNG.</li>
        </ul>
        <p>Need to make a change? Use the "Do Over" feature here.<br>
        <a href="https://qrforus.com/do-over">https://qrforus.com/do-over</a></p>
        <p>Thanks for using QR for US™ — we connect real-life moments to the digital world.</p>
        <p><strong>QR for US™</strong><br>Scan it. Click it. Share your story.<br><a href="https://qrforus.com">https://qrforus.com</a></p>
        """

        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            files=[("attachment", ("qr_code.png", img_data))],
            data={"from": FROM_EMAIL,
                  "to": TO_EMAIL,
                  "subject": "Your QR for US™ code is ready to use!",
                  "html": html})

        print("📤 Mailgun response:", response.status_code, response.text)
        return jsonify({"message": "QR Code generated and sent via email."}), 200

    except Exception as e:
        print("❌ Error:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
