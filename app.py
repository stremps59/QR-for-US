import os
import qrcode
import io
import base64
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib

app = Flask(__name__)
CORS(app)

MAILGUN_API_KEY = os.environ.get("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.environ.get("MAILGUN_DOMAIN")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")

def generate_qr_code(data, fill_color="black", back_color="white"):
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=5
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fill_color, back_color=back_color).convert('RGB')
    return img

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    try:
        content = request.json
        data = content.get('data', '')
        email = content.get('email', '')
        filename = content.get('filename', 'qr_code')
        fill_color = content.get('fill_color', 'black')
        back_color = content.get('back_color', 'white')

        img = generate_qr_code(data, fill_color, back_color)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        # Create email
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = email
        msg['Subject'] = "Your QR for US™ Code is Ready!"

        body = MIMEText("""Thanks for using QR for US™!

Your QR code is attached and ready to use.

You can scan it or click on it to visit your link. Your code is valid for 30 days (or as long as your subscription is active). Save it anywhere — on a business card, pet tag, wedding invite, resume, or product packaging.

Need changes? Just reply to this email. Want to build your own landing page? We recommend Carrd™ — it’s simple and powerful.

Thanks again!
QR for US™ Team
""")
        msg.attach(body)

        part = MIMEApplication(img_byte_arr.read(), Name=f"{filename}.png")
        part['Content-Disposition'] = f'attachment; filename="{filename}.png"'
        msg.attach(part)

        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages.mime",
            auth=("api", MAILGUN_API_KEY),
            files={"message": ("message.mime", msg.as_string())}
        )

        if response.status_code == 200:
            return jsonify({'message': 'QR code sent successfully'}), 200
        else:
            return jsonify({'error': 'Failed to send email', 'details': response.text}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
