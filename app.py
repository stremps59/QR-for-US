
from flask import Flask, request, jsonify, send_file
from flask_mail import Mail, Message
import qrcode
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os

app = Flask(__name__)

# Email configuration from environment variables
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

mail = Mail(app)

@app.route('/generate-qr', methods=['POST'])
def generate_qr():
    data = request.get_json()
    url = data.get('url')
    email = data.get('email')
    message = data.get('message', 'Thank you for using QR for US!')

    if not url or not email:
        return jsonify({'error': 'Missing url or email'}), 400

    # Generate QR code
    qr = qrcode.make(url)
    img_io = io.BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)

    # Generate PDF with QR code
    pdf_io = io.BytesIO()
    c = canvas.Canvas(pdf_io, pagesize=letter)
    c.drawString(100, 750, f"QR Code for: {url}")
    c.drawImage(ImageReader(img_io), 100, 500, width=200, height=200)
    c.save()
    pdf_io.seek(0)

    # Email with both QR image and PDF
    msg = Message('Your QR Code from QR for US', recipients=[email])
    msg.body = f"{message}

Scan the QR or click the image below:
{url}"
    msg.attach('qr_code.png', 'image/png', img_io.getvalue())
    msg.attach('qr_code.pdf', 'application/pdf', pdf_io.getvalue())

    try:
        mail.send(msg)
        return jsonify({'message': 'QR Code sent successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
