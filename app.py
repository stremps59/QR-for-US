
from flask import Flask, request, jsonify
from flask_mail import Mail, Message
import qrcode
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image

app = Flask(__name__)

# Email Configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT'))
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS') == 'True'
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL') == 'True'
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

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
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Save PNG to memory
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    # Generate PDF with QR code
    pdf_io = BytesIO()
    c = canvas.Canvas(pdf_io, pagesize=letter)
    c.drawString(100, 750, "Scan the QR code below:")
    c.drawImage(ImageReader(BytesIO(img_io.getvalue())), 100, 500, width=200, height=200)
    c.save()
    pdf_io.seek(0)

    # Send email
    msg = Message("Your QR Code", recipients=[email])
    msg.body = message
    msg.attach("qr_code.png", "image/png", img_io.getvalue())
    msg.attach("qr_code.pdf", "application/pdf", pdf_io.getvalue())

    mail.send(msg)

    return jsonify({'status': 'QR Code sent successfully'})

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=10000)
