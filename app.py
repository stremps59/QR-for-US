
import os
import io
import base64
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import qrcode
from qrcode.image.styles.moduledrawers import SquareModuleDrawer
from PIL import Image, ImageColor
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

app = Flask(__name__)
CORS(app)

MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
MAILGUN_FROM = os.getenv("MAILGUN_FROM", "QR for US <qrforus@sandbox.mailgun.org>")

def parse_color(color_str):
    try:
        return ImageColor.getrgb(color_str)
    except Exception:
        return (0, 0, 0)

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    try:
        data = request.json
        url = data.get('url', '')
        email = data.get('email', '')
        dot_color = parse_color(data.get('dot_color', 'black'))
        bg_color = parse_color(data.get('bg_color', 'white'))

        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=4
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color=dot_color, back_color=bg_color, image_factory=qrcode.image.pil.PilImage, module_drawer=SquareModuleDrawer())

        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        qr_code_png = buffered.getvalue()

        msg = MIMEMultipart()
        msg['From'] = MAILGUN_FROM
        msg['To'] = email
        msg['Subject'] = "Your QR Code from QR for US™"

        body = MIMEText("Thanks for using QR for US™! Your QR code is attached and ready to use.

Simply scan or click to verify.

If you selected a 'Custom' option, your QR will visually reflect that.", 'plain')
        msg.attach(body)

        part = MIMEApplication(qr_code_png, Name="qr_code.png")
        part['Content-Disposition'] = 'attachment; filename="qr_code.png"'
        msg.attach(part)

        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            files={"attachment": ("qr_code.png", qr_code_png)},
            data={"from": MAILGUN_FROM,
                  "to": [email],
                  "subject": "Your QR Code from QR for US™",
                  "text": "Thanks for using QR for US™! Your QR code is attached and ready to use.

Simply scan or click to verify.

If you selected a 'Custom' option, your QR will visually reflect that."}
        )

        if response.status_code != 200:
            return jsonify({'error': 'Mailgun delivery failed', 'details': response.text}), 500

        return jsonify({'message': 'QR code generated and email sent successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
