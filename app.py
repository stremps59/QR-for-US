
import os
import qrcode
import base64
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
from io import BytesIO
import random
import string

app = Flask(__name__)
CORS(app)

MAILGUN_API_KEY = os.environ.get("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.environ.get("MAILGUN_DOMAIN")
FROM_EMAIL = os.environ.get("FROM_EMAIL")

def generate_unique_id(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def send_email_with_attachment(to_email, name, image_data, unique_id, destination_url):
    url = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"
    auth = ("api", MAILGUN_API_KEY)

    subject = "Your QR for US™ QR code is ready to use!"
    attachment = ("qr_code.png", image_data, "image/png")

    html_content = f"""
    <p>Hi {name},</p>
    <p>Your QR Code is ready!</p>
    <p>It's attached to this email as a PNG image — ready to use in print, online, and everywhere in between.</p>

    <p>You can use this single code in three powerful ways:</p>
    <ol>
      <li><strong>Scannable</strong><br>
      Print or display the image. It can be scanned instantly by any smartphone camera — no app required.<br>
      Use it on resumes, posters, name badges, pet tags, product packaging, signs, and more.</li>

      <li><strong>Clickable</strong><br>
      Want to use it in a document or email? Easy.<br>
      <ul>
        <li>Insert the PNG image anywhere.</li>
        <li>Right-click it and choose “Add Hyperlink” or “Insert Link.”</li>
        <li>Paste your destination URL.</li>
      </ul>
      That's it — now it's clickable too.</li>

      <li><strong>Saveable</strong><br>
      Right-click the image and select “Save As” to store it.<br>
      Use it again whenever and wherever you need.</li>
    </ol>

    <p><a href="https://qrforus.com/do-over?id={unique_id}">Need to change the color, shape, or style? Click here to regenerate your QR (up to 2 times within 24 hours).</a></p>

    <p><em>QR for US™ connects your stories, profiles, and passions to the world — one QR at a time.<br>
    This code is your bridge between digital life and real-life moments.</em></p>

    <p>Have questions or want help with creative ideas? Reach us at <a href="mailto:qrforus1@gmail.com">qrforus1@gmail.com</a></p>

    <p>—<br>
    QR for US™<br>
    Scan it. Click it. Share your story.<br>
    <a href="https://qrforus.com">https://qrforus.com</a></p>
    """

    response = requests.post(url, auth=auth, files={"attachment": attachment}, data={
        "from": FROM_EMAIL,
        "to": to_email,
        "subject": subject,
        "html": html_content
    })

    print(f"📤 Mailgun response: {response.status_code} {response.text}")
    return response

@app.route("/generate_qr", methods=["POST"])
def generate_qr():
    try:
        data = request.json.get("data", {}).get("data", {}).get("fields", [])
        print("📦 Raw incoming data:", request.json)

        parsed_data = {field.get("label", ""): field.get("value") for field in data}

        name = parsed_data.get("First Name", "Customer")
        email = parsed_data.get("Email address")
        destination = parsed_data.get("Where should your QR Code point (Website/URL)?")
        if not destination:
            print("⚠️ Missing destination URL.")
            return jsonify({"error": "Destination URL missing."}), 400

        unique_id = generate_unique_id()

        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
        qr.add_data(destination)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        img_buffer = BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        send_email_with_attachment(email, name, img_buffer.read(), unique_id, destination)
        return jsonify({"status": "success"}), 200

    except Exception as e:
        print("❌ Error generating QR or sending email:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
