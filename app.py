
import os
import qrcode
import requests
from flask import Flask, request, jsonify
from io import BytesIO
import base64

app = Flask(__name__)

MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
MAILGUN_FROM = f"QR for US <qrforus@{MAILGUN_DOMAIN}>"

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    data = request.json
    user_email = data.get('email')
    target_url = data.get('url')

    if not user_email or not target_url:
        return jsonify({"error": "Missing email or URL"}), 400

    # Generate QR code
    qr = qrcode.make(target_url)
    qr_img_io = BytesIO()
    qr.save(qr_img_io, 'PNG')
    qr_img_io.seek(0)

    # Encode image for inline HTML embedding
    img_base64 = base64.b64encode(qr_img_io.getvalue()).decode('utf-8')
    qr_img_io.seek(0)

    html_body = f"""
    <html>
        <body>
            <h2>Your QR Code</h2>
            <p>📱 <b>Scan it:</b> Use your phone camera to scan the image below.</p>
            <p>🖱️ <b>Click it:</b> This image is also clickable — test it now!</p>
            <p>🖨️ <b>Print it:</b> The attached image is high-quality and ready to print.</p>
            <p>💾 <b>Reuse it:</b></p>
            <ul>
                <li>Right-click and save the image below.</li>
                <li>Use it in your email signature, LinkedIn profile, website, or business card.</li>
                <li><b>To keep it clickable</b>, be sure to link it to:<br>
                <code>{target_url}</code></li>
            </ul>
            <p><a href="{target_url}">
                <img src="data:image/png;base64,{img_base64}" alt="QR Code" style="max-width:300px;">
            </a></p>
        </body>
    </html>
    """

    # Send via Mailgun API
    response = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        files=[
            ("attachment", ("qrcode.png", qr_img_io, "image/png")),
        ],
        data={
            "from": MAILGUN_FROM,
            "to": [user_email],
            "subject": "Your QR Code from QR for US",
            "html": html_body
        },
    )

    if response.status_code != 200:
        return jsonify({"error": "Email failed", "details": response.text}), 500

    return jsonify({"message": "QR code generated and emailed successfully."})

if __name__ == '__main__':
    app.run(debug=True)
