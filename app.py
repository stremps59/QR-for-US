
from flask import Flask, request, jsonify
import qrcode
from reportlab.pdfgen import canvas
from flask_mail import Mail, Message
import os
import smtplib

app = Flask(__name__)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

mail = Mail(app)

@app.route('/generate-qr', methods=['POST'])
def generate_qr():
    data = request.json
    url = data.get('url')
    email = data.get('email')

    if not url or not email:
        return jsonify({'error': 'Missing URL or email'}), 400

    try:
        # Generate QR code (PNG)
        img = qrcode.make(url)
        png_path = 'qr_code.png'
        img.save(png_path)

        # Generate PDF with QR code
        pdf_path = 'qr_code.pdf'
        c = canvas.Canvas(pdf_path)
        c.drawImage(png_path, 100, 500, width=300, height=300)
        c.drawString(100, 480, f"Scan or click this code to visit: {url}")
        c.save()

        # Log email connection attempt
        print("Attempting to send email via:")
        print(f"MAIL_SERVER: {app.config['MAIL_SERVER']}")
        print(f"MAIL_PORT: {app.config['MAIL_PORT']}")
        print(f"MAIL_USE_TLS: {app.config['MAIL_USE_TLS']}")
        print(f"MAIL_USERNAME: {app.config['MAIL_USERNAME']}")

        # Email the files
        msg = Message("Your QR Code from QR for US", recipients=[email])
        msg.body = f"Hi! Your QR code is ready. It links to:\n{url}"
        with open(png_path, 'rb') as png_file:
            msg.attach("qr_code.png", "image/png", png_file.read())
        with open(pdf_path, 'rb') as pdf_file:
            msg.attach("qr_code.pdf", "application/pdf", pdf_file.read())
        mail.send(msg)

        return jsonify({'message': 'QR code sent successfully'}), 200

    except Exception as e:
        print("Exception occurred:", str(e))
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
