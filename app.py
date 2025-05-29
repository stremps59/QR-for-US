
import os
import io
import qrcode
from flask import Flask, request, jsonify
from flask_mail import Mail, Message
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from email.mime.image import MIMEImage

app = Flask(__name__)

# Email configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS') == 'True'
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

mail = Mail(app)

@app.route('/generate-qr', methods=['POST'])
def generate_qr():
    data = request.get_json()
    url = data.get('url')
    email = data.get('email')

    if not url or not email:
        return jsonify({'error': 'Missing URL or email'}), 400

    # Generate QR code
    qr = qrcode.make(url)
    img_io = io.BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)

    # Create PDF
    pdf_io = io.BytesIO()
    c = canvas.Canvas(pdf_io, pagesize=letter)
    c.drawImage(ImageReader(img_io), 100, 500, width=200, height=200)
    c.drawString(100, 480, url)
    c.save()
    pdf_io.seek(0)

    # Compose email
    msg = Message(subject="Your QR for US Code", recipients=[email])
    msg.html = f'''
    <p>Here is your custom QR code:</p>
    <a href="{url}"><img src="cid:qrimage" alt="QR Code" style="width:200px;height:200px;"/></a>
    <p>If you can't scan it, just <a href="{url}">click here</a>.</p>
    <p>Or copy and paste this link: {url}</p>
    '''

    # Attach PNG image as inline
    image = MIMEImage(img_io.read(), 'png')
    image.add_header('Content-ID', '<qrimage>')
    image.add_header('Content-Disposition', 'inline', filename='qr.png')
    msg.attach(image)

    # Attach PDF
    msg.attach('qr_code.pdf', 'application/pdf', pdf_io.read())

    mail.send(msg)
    return jsonify({'message': 'QR Code sent successfully'})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=10000)
