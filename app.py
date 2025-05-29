
from flask import Flask, request, jsonify
from flask_mail import Mail, Message
import qrcode
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import base64

app = Flask(__name__)

# Email configuration from environment variables
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)

@app.route('/generate-qr', methods=['POST'])
def generate_qr():
    data = request.json
    url = data.get('url')
    email = data.get('email')
    message = data.get('message', '')

    if not url or not email:
        return jsonify({'error': 'Missing url or email'}), 400

    # Generate QR code
    qr = qrcode.make(url)
    img_io = BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)

    # Generate PDF
    pdf_io = BytesIO()
    c = canvas.Canvas(pdf_io, pagesize=letter)
    c.drawImage(ImageReader(BytesIO(img_io.getvalue())), 100, 500, width=200, height=200)
    c.drawString(100, 480, url)
    c.save()
    pdf_io.seek(0)

    # Email with attachments
    msg = Message('Your QR Code', sender=app.config['MAIL_USERNAME'], recipients=[email])
    msg.body = f"{message}"
    msg.attach("qr_code.png", "image/png", img_io.getvalue())
    msg.attach("qr_code.pdf", "application/pdf", pdf_io.getvalue())

    mail.send(msg)

    return jsonify({'message': 'QR code sent successfully'})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=10000)
