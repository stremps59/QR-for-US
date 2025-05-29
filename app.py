from flask import Flask, request, jsonify
from flask_mail import Mail, Message
import qrcode
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import base64

app = Flask(__name__)

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.mail.att.net'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'stremps@sbcglobal.net'
app.config['MAIL_PASSWORD'] = 'your_secure_key_here'

mail = Mail(app)

@app.route('/generate-qr', methods=['POST'])
def generate_qr():
    data = request.get_json()
    email = data.get('email')
    link = data.get('link')
    message = data.get('message', '')

    if not email or not link:
        return jsonify({'error': 'Missing email or link'}), 400

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Save QR as image in memory
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    # Embed QR in PDF
    pdf_io = BytesIO()
    c = canvas.Canvas(pdf_io, pagesize=letter)
    c.drawString(100, 750, "QR Code")
    c.drawImage(ImageReader(BytesIO(img_io.getvalue())), 100, 500, width=200, height=200)
    c.save()
    pdf_io.seek(0)

    # Convert QR to base64 for embedding in HTML
    qr_b64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
    qr_img_html = f'<a href="{link}" target="_blank"><img src="data:image/png;base64,{qr_b64}" alt="QR Code" style="width:200px;height:200px;"></a>'

    # Final HTML email body
    msg = Message("Your QR Code from QR for US", recipients=[email])
    msg.body = f"{message}\n\nAttached is your QR code as a PDF and PNG."
    msg.html = f"""
        <p>Attached is your custom QR code in both PNG and PDF formats.</p>

        <h3>🔗 Clickable & Scanable? Yes!</h3>
        <p>This QR is digital-first, which means:</p>
        <ul>
          <li>You can <strong>click the QR image directly in this email</strong> — it acts like a smart link!</li>
          <li>You can <strong>scan it using any phone camera</strong> — like a traditional QR code.</li>
        </ul>
        <p>Either way, it leads to the same destination: your personalized digital page.</p>

        <h4>📌 To Use It:</h4>
        <ol>
          <li><strong>Sharing Digitally (Email, Social Media, or Web):</strong>
            <ul>
              <li>The PNG image is <strong>clickable</strong> by default in most email clients and messaging apps.</li>
              <li>To post on social media or your website:
                <ul>
                  <li>Upload the PNG image.</li>
                  <li>Add a hyperlink to your QR destination if your platform allows it (optional).</li>
                </ul>
              </li>
              <li>Add it to digital resumes, business cards, newsletters, event pages, or even your email signature.</li>
            </ul>
          </li>
          <li><strong>Using It In Print:</strong>
            <ul>
              <li>Use the PDF file for high-resolution printing.</li>
              <li>It’s perfect for posters, flyers, product labels, cards, packaging, and more.</li>
              <li>Anyone can scan it using a phone camera or QR reader app.</li>
            </ul>
          </li>
        </ol>

        <p><em>🧠 Tip: Think of your QR code as both a button and a barcode. Click it or scan it — it just works.</em></p>

        <p>Thank you again for choosing <strong>QR for US</strong>. We’re honored to help tell your story.</p>

        <p>– The QR for US Team</p>

        {qr_img_html}
    """
    msg.attach("qr_code.pdf", "application/pdf", pdf_io.getvalue())

    mail.send(msg)

    return jsonify({"status": "QR code sent successfully"})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=10000)