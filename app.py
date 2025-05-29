
from flask import Flask, request, jsonify
from flask_mail import Mail, Message
import qrcode
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import base64
import os

app = Flask(__name__)

# Email configuration using environment variables
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

mail = Mail(app)

@app.route('/generate-qr', methods=['POST'])
def generate_qr():
    data = request.get_json()
    url = data['url']
    recipient = data['email']
    subject = data.get('subject', 'Your QR Code')
    message = data.get('message', 'Here is your QR code.')

    # Generate QR image
    qr = qrcode.make(url)
    img_io = io.BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)
    img_data = img_io.read()
    img_b64 = base64.b64encode(img_data).decode('utf-8')

    # Generate PDF with QR
    pdf_io = io.BytesIO()
    c = canvas.Canvas(pdf_io, pagesize=letter)
    c.drawInlineImage(qr, 100, 500, width=200, height=200)
    c.showPage()
    c.save()
    pdf_io.seek(0)

    # Compose email
    msg = Message(subject, recipients=[recipient])
    msg.body = f"{message}

Scan the QR or click the image below:
{url}"
    msg.html = f"""
    <p>{message}</p>
    <p><a href="{url}"><img src="cid:qr_image" alt="QR Code"></a></p>
    <p>Or click here: <a href="{url}">{url}</a></p>
    """

    msg.attach("qr_code.pdf", "application/pdf", pdf_io.read())
    msg.attach("qr_code.png", "image/png", img_data, 'inline', headers=[['Content-ID', '<qr_image>']])

    mail.send(msg)

    return jsonify({'status': 'QR code sent successfully'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
