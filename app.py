
import os
import qrcode
import pdfkit
import requests
from flask import Flask, request, jsonify
from io import BytesIO

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

    # Generate PDF
    html_content = f"<html><body><h2>Your QR Code</h2><p>{target_url}</p></body></html>"
    pdf_io = BytesIO(pdfkit.from_string(html_content, False))

    # Send via Mailgun API
    response = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        files=[
            ("attachment", ("qrcode.png", qr_img_io, "image/png")),
            ("attachment", ("qrcode.pdf", pdf_io, "application/pdf")),
        ],
        data={
            "from": MAILGUN_FROM,
            "to": [user_email],
            "subject": "Your QR Code from QR for US",
            "text": f"Attached is your QR code for {target_url}."
        },
    )

    if response.status_code != 200:
        return jsonify({"error": "Email failed", "details": response.text}), 500

    return jsonify({"message": "QR code generated and emailed successfully."})

if __name__ == '__main__':
    app.run(debug=True)
