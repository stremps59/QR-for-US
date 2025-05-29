import os
import qrcode
from flask import Flask, request, jsonify
from flask_mail import Mail, Message
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

app = Flask(__name__)

# Configure mail
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)

@app.route("/generate-qr", methods=["POST"])
def generate_qr():
    data = request.get_json()
    url = data.get("url")
    recipient = data.get("email")
    message = data.get("message", "Here is your QR code!")

    if not url or not recipient:
        return jsonify({"error": "Missing required parameters"}), 400

    # Generate QR code
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Save QR code to a BytesIO stream
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    # Create a PDF with the QR code and clickable text
    pdf_io = BytesIO()
    c = canvas.Canvas(pdf_io, pagesize=letter)
    c.drawImage(ImageReader(BytesIO(img_io.getvalue())), 100, 500, width=200, height=200)
    c.linkURL(url, (100, 480, 300, 500), relative=0, thickness=1)
    c.drawString(100, 480, "Click or scan the QR code to visit your link!")
    c.save()
    pdf_io.seek(0)

    # Create email message
    msg = Message("Your QR for US code", sender=app.config['MAIL_USERNAME'], recipients=[recipient])
    msg.body = f"""{message}

The attached QR code is both scannable and clickable:
- You can scan it with your phone camera.
- Or click the link in the attached PDF.

To reuse it elsewhere:
1. Download and save the QR code attachment.
2. You may insert it into documents, presentations, or emails.
3. Remember: The clickable version (PDF) is also scannable!

Thank you for choosing QR for US. We're honored to be part of your story."""

    msg.attach("qr_code.png", "image/png", img_io.getvalue())
    msg.attach("qr_code.pdf", "application/pdf", pdf_io.getvalue())

    mail.send(msg)

    return jsonify({"message": "QR code sent successfully"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)