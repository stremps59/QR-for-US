
import os
import io
import uuid
import base64
import qrcode
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# Load environment variables with default values
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY", "")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN", "")
MAILGUN_FROM = os.getenv("MAILGUN_FROM", f"mailgun@{MAILGUN_DOMAIN}")

@app.route("/")
def home():
    return "QR for US backend is running"

@app.route("/generate_qr", methods=["POST"])
def generate_qr():
    try:
        data = request.json or {}
        fields = data.get("data", {}).get("fields", [])

        # Extract field values with fallback
        def get_field(label, default=""):
            for field in fields:
                if isinstance(field, dict) and field.get("label", "").strip().lower() == label.strip().lower():
                    return field.get("value", default)
            return default

        first_name = get_field("First Name", "")
        email = get_field("Email address", "")
        destination = get_field("Where should your QR Code point (Website/URL)?", "https://qrforus.com")

        # Set default QR styling colors
        border_color = get_field("Border Color (HEX# or Named color)", "black")
        dot_color = get_field("Corner finder dots color (HEX# or Named color)", "black")
        center_color = get_field("Center image color (if no image uploaded; HEX# or Named color)", "black")
        data_color = get_field("Data modules color (HEX# or Named color)", "black")

        # Generate QR
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
        qr.add_data(destination)
        qr.make(fit=True)
        img = qr.make_image(fill_color=data_color, back_color="white").convert("RGB")

        # Convert to bytes
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        # Compose HTML email
        html_body = f""" 
        <p>Hi {first_name},</p>
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
        <a href="https://qrforus.com/do-over?id={uuid.uuid4().hex[:8]}">https://qrforus.com/do-over?id={uuid.uuid4().hex[:8]}</a></p>
        <p>QR for US™ connects your stories, profiles, and passions to the world -- one QR at a time.<br>
        This code is your bridge between digital life and real-life moments.</p>
        <p>Have questions or want help with creative ideas? Reach us at qrforus1@gmail.com</p>
        <hr>
        <p><strong>QR for US™<br>
        Scan it. Click it. Share your story.<br>
        <a href="https://qrforus.com">https://qrforus.com</a></strong></p>
        """

        # Check if Mailgun API key and domain are set
        if not MAILGUN_API_KEY or not MAILGUN_DOMAIN:
            return jsonify({"error": "Mailgun API key and domain are not configured"}), 500

        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            files={"attachment": ("qr.png", buffered.getvalue())},
            data={
                "from": MAILGUN_FROM,
                "to": email,
                "subject": "Your QR for US™ code is ready to use!",
                "html": html_body
            },
        )

        return jsonify({"message": "QR code sent", "mailgun": response.text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
