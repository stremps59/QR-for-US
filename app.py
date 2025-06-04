
from flask import Flask, request, jsonify
import qrcode
import io
import base64
import os
import uuid
import requests
import traceback
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def home():
    return "QR for US is running!"

@app.route("/generate_qr", methods=["POST"])
def generate_qr():
    try:
        data = request.get_json()
        print("📦 Raw incoming data:", data)

        fields = {field['label'].strip().lower(): field['value'] for field in data.get("data", {}).get("fields", [])}

        name = fields.get("first name", "QR User")
        email = fields.get("email address")
        destination = fields.get("where should your qr code point (website/url)")
        qr_type = fields.get("what type of qr would you like?", ["standard"])
        if isinstance(qr_type, list):
            qr_type = qr_type[0]
        else:
            qr_type = "standard"
        color = fields.get("data modules color (hex# or named color)", "black")
        shape = fields.get("what border style would you like?", ["square"])
        if isinstance(shape, list):
            shape = shape[0]
        else:
            shape = "square"

        logo = None  # optional upload
        print(f"🧾 Parsed - name: {name}, email: {email}, destination: {destination}")

        # QR generation
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(destination or "https://qrforus.com")
        qr.make(fit=True)
        img = qr.make_image(fill_color=color, back_color="white").convert("RGB")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

        qr_id = str(uuid.uuid4())[:8]
        do_over_link = f"https://qrforus.com/do-over?id={qr_id}"

        MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
        MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
        FROM_EMAIL = os.getenv("FROM_EMAIL")

        print(f"🔐 ENV - API Key Present: {bool(MAILGUN_API_KEY)}, Domain: {MAILGUN_DOMAIN}, From: {FROM_EMAIL}, To: {email}")

        if MAILGUN_API_KEY and MAILGUN_DOMAIN and FROM_EMAIL and email:
            try:
                html_body = f"""<p>Hi {name},</p>
<p></p>
<p>Your QR Code is ready!</p>
<p>It&#x27;s attached to this email as a PNG image -- ready to use in print, online, and everywhere in between.</p>
<p></p>
<p>You can use this single code in three powerful ways:</p>
<p></p>
<p>1. Scanable</p>
<p>Print or display the image. It can be scanned instantly by any smartphone camera -- no app required.</p>
<p>Use it on resumes, posters, name badges, pet tags, product packaging, signs, and more.</p>
<p></p>
<p>2. Clickable</p>
<p>Want to use it in a document or email? Easy.</p>
<p>- Insert the PNG image anywhere.</p>
<p>- Right-click it and choose &quot;Add Hyperlink&quot; or &quot;Insert Link.&quot;</p>
<p>- Paste your destination URL.</p>
<p>That&#x27;s it -- now it&#x27;s clickable too.</p>
<p></p>
<p>3. Saveable</p>
<p>Right-click the image and select &quot;Save As&quot; to store it.</p>
<p>Use it again whenever and wherever you need.</p>
<p></p>
<p>Need to change the color, shape, or style?</p>
<p>Click below to regenerate your QR (up to 2 times within 24 hours):</p>
<p><a href='{do_over_link}'>Do Over Link</a></p>
<p></p>
<p>QR for US(TM) connects your stories, profiles, and passions to the world -- one QR at a time.</p>
<p>This code is your bridge between digital life and real-life moments.</p>
<p></p>
<p>Have questions or want help with creative ideas? Reach us at qrforus1@gmail.com</p>
<p></p>
<p>--</p>
<p>QR for US(TM)</p>
<p>Scan it. Click it. Share your story.</p>
<p>https://qrforus.com</p>"""
                print("📧 Email HTML:", html_body)

                response = requests.post(
                    f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
                    auth=("api", MAILGUN_API_KEY),
                    data={
                        "from": FROM_EMAIL,
                        "to": email,
                        "subject": "Your QR Code is Ready",
                        "html": html_body
                    }
                )
                print("📤 Mailgun response:", response.status_code, response.text)
            except Exception as e:
                print("❌ Exception while sending email:")
                traceback.print_exc()

        return jsonify({
            "message": "QR created",
            "clickable_image": f"data:image/png;base64,{img_str}",
            "do_over_link": do_over_link
        })

    except Exception as err:
        print("🔥 Top-level error caught:")
        traceback.print_exc()
        return jsonify({"error": str(err)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
