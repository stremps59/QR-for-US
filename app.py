
import os
import io
import base64
import requests
import qrcode
from PIL import Image
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

MAILGUN_API_KEY = os.environ.get('MAILGUN_API_KEY')
MAILGUN_DOMAIN = os.environ.get('MAILGUN_DOMAIN')
FROM_EMAIL = os.environ.get('FROM_EMAIL')

@app.route("/generate_qr", methods=["POST"])
def generate_qr():
    try:
        data = request.json
        print("📦 Raw incoming data:", data)

        fields = data.get("data", {}).get("fields", [])

        def get_field(label):
            for field in fields:
                if field.get("label") == label:
                    return field.get("value")
            return None

        name = get_field("First Name") or "Friend"
        email = get_field("Email address")
        raw_dest = get_field("Where should your QR Code point (Website/URL)?")

        # Normalize destination from list or string
        if isinstance(raw_dest, list):
            destination = raw_dest[0] if raw_dest else "https://qrforus.com"
        else:
            destination = raw_dest or "https://qrforus.com"

        print(f"🧾 Parsed - name: {name}, email: {email}, destination: {destination}")

        # Generate QR code
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(destination)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        # Save QR to buffer
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        encoded_image = base64.b64encode(buffer.read()).decode("utf-8")

        # Compose HTML email
        email_html = f"""<p>Hi {name},</p>
<p>Your QR Code is ready!</p>
<p>It's attached to this email as a PNG image -- ready to use in print, online, and everywhere in between.</p>
<p>You can use this single code in three powerful ways:</p>
<ol>
  <li><strong>Scanable</strong><br>
  Print or display the image. It can be scanned instantly by any smartphone camera -- no app required.<br>
  Use it on resumes, posters, name badges, pet tags, product packaging, signs, and more.</li>
  <li><strong>Clickable</strong><br>
  Want to use it in a document or email? Easy.<br>
  - Insert the PNG image anywhere.<br>
  - Right-click it and choose "Add Hyperlink" or "Insert Link."<br>
  - Paste your destination URL.<br>
  That's it -- now it's clickable too.</li>
  <li><strong>Saveable</strong><br>
  Right-click the image and select "Save As" to store it.<br>
  Use it again whenever and wherever you need.</li>
</ol>
<p>Need to change the color, shape, or style?<br>
Click below to regenerate your QR (up to 2 times within 24 hours):<br>
<a href='https://qrforus.com/do-over?id=12345678'>https://qrforus.com/do-over?id=12345678</a></p>
<p>QR for US™ connects your stories, profiles, and passions to the world -- one QR at a time.<br>
This code is your bridge between digital life and real-life moments.</p>
<p>Have questions or want help with creative ideas? Reach us at qrforus1@gmail.com</p>
<hr>
<p><strong>QR for US™<br>
Scan it. Click it. Share your story.<br>
<a href='https://qrforus.com'>https://qrforus.com</a></strong></p>
"""

        print("📧 Email HTML:", email_html[:500])  # print a preview only

        # Send with Mailgun
        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            files={"attachment": ("qr.png", base64.b64decode(encoded_image))},
            data={
                "from": FROM_EMAIL,
                "to": email,
                "subject": "Your QR for US Code is Ready!",
                "html": email_html
            },
        )

        print("📤 Mailgun response:", response.status_code, response.text)
        return jsonify({"message": "QR code sent!"})

    except Exception as e:
        print("❌ Error:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=10000)
