
import os
from flask import Flask, request, jsonify, send_file
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from flask_mail import Mail, Message

app = Flask(__name__)

# Email config
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', '1', 't']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

mail = Mail(app)

@app.route("/generate-qr", methods=["POST"])
def generate_qr():
    data = request.json
    url = data.get("url")
    email = data.get("email")
    message = data.get("message", "")

    if not url or not email:
        return jsonify({"error": "Missing 'url' or 'email'"}), 400

    # Generate QR code
    qr = qrcode.make(url)
    qr_io = BytesIO()
    qr.save(qr_io, 'PNG')
    qr_io.seek(0)

    # Create PDF with QR code and clickable link
    pdf_io = BytesIO()
    c = canvas.Canvas(pdf_io, pagesize=letter)
    c.drawImage(ImageReader(qr_io), 200, 500, width=200, height=200)
    c.setFillColorRGB(0, 0, 1)
    c.linkURL(url, (200, 500, 400, 700), relative=0)
    c.drawString(200, 480, url)
    c.save()
    pdf_io.seek(0)

    # Send email with both PNG and PDF
    msg = Message("Your QR Code from QR for US", recipients=[email])
    msg.body = f"{message}

Scan the QR or click the image below:
{url}"
    msg.attach("qr_code.png", "image/png", qr_io.getvalue())
    msg.attach("qr_code.pdf", "application/pdf", pdf_io.getvalue())
    mail.send(msg)

    return jsonify({"message": "QR Code sent successfully"}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=10000)
