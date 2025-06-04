
import os
import io
import base64
import uuid
import traceback
import requests
import qrcode
from flask import Flask, request, jsonify
from flask_cors import CORS
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def home():
    return "QR for US is running!"

@app.route("/generate_qr", methods=["POST"])
def generate_qr():
    try:
        data = request.get_json()
        fields = {field['label'].strip().lower(): field['value'] for field in data.get("data", {}).get("fields", [])}
        name = fields.get("first name", "QR User")
        email = fields.get("email address")
        destination = fields.get("where should your qr code point (website/url)")
        color = fields.get("data modules color (hex# or named color)", "black")

        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
        qr.add_data(destination or "https://qrforus.com")
        qr.make(fit=True)
        img = qr.make_image(fill_color=color.strip(), back_color="white").convert("RGB")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

        qr_id = str(uuid.uuid4())[:8]
        do_over_link = f"https://qrforus.com/do-over?id={qr_id}"

        MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
        MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
        FROM_EMAIL = os.getenv("FROM_EMAIL")

        if MAILGUN_API_KEY and MAILGUN_DOMAIN and FROM_EMAIL and email:
            try:
                # Full plain text
                text_body = f"""Hi {name},
Your QR Code is ready!
It's attached to this email as a PNG image -- ready to use in print, online, and everywhere in between.

You can use this single code in three powerful ways:

1. Scanable
Print or display the image. It can be scanned instantly by any smartphone camera -- no app required.
Use it on resumes, posters, name badges, pet tags, product packaging, signs, and more.

2. Clickable
Want to use it in a document or email? Easy.
- Insert the PNG image anywhere.
- Right-click it and choose "Add Hyperlink" or "Insert Link."
- Paste your destination URL.
That's it -- now it's clickable too.

3. Saveable
Right-click the image and select "Save As" to store it.
Use it again whenever and wherever you need.

Need to change the color, shape, or style?
Click below to regenerate your QR (up to 2 times within 24 hours):
{do_over_link}

QR for US(TM) connects your stories, profiles, and passions to the world -- one QR at a time.
This code is your bridge between digital life and real-life moments.

Have questions or want help with creative ideas? Reach us at qrforus1@gmail.com

--
QR for US(TM)
Scan it. Click it. Share your story.
https://qrforus.com"""

                # HTML version
                html_body = f"""<html>
  <body style='font-family: Arial, sans-serif; font-size: 16px; color: #333;'>
    <p>Hi {name},</p>
    <p>Your QR Code is ready!<br>
    It's attached to this email as a PNG image -- ready to use in print, online, and everywhere in between.</p>

    <p>You can use this single code in three powerful ways:</p>
    <ol>
      <li><strong>Scanable</strong><br>
        Print or display the image. It can be scanned instantly by any smartphone camera -- no app required.<br>
        Use it on resumes, posters, name badges, pet tags, product packaging, signs, and more.
      </li>
      <li><strong>Clickable</strong><br>
        Want to use it in a document or email? Easy.<br>
        - Insert the PNG image anywhere.<br>
        - Right-click it and choose "Add Hyperlink" or "Insert Link."<br>
        - Paste your destination URL.<br>
        That's it -- now it's clickable too.
      </li>
      <li><strong>Saveable</strong><br>
        Right-click the image and select "Save As" to store it.<br>
        Use it again whenever and wherever you need.
      </li>
    </ol>

    <p>Need to change the color, shape, or style?<br>
    Click below to regenerate your QR (up to 2 times within 24 hours):<br>
    <a href="{do_over_link}">{do_over_link}</a></p>

    <p>QR for US(TM) connects your stories, profiles, and passions to the world -- one QR at a time.<br>
    This code is your bridge between digital life and real-life moments.</p>

    <p>Have questions or want help with creative ideas? Reach us at <a href="mailto:qrforus1@gmail.com">qrforus1@gmail.com</a></p>

    <hr>
    <p><strong>QR for US(TM)</strong><br>
    Scan it. Click it. Share your story.<br>
    <a href="https://qrforus.com">https://qrforus.com</a></p>
  </body>
</html>"""

                response = requests.post(
                    f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
                    auth=("api", MAILGUN_API_KEY),
                    data={
                        "from": FROM_EMAIL,
                        "to": email,
                        "subject": "Your QR for US(TM) QR Code is Ready to Use!",
                        "text": text_body,
                        "html": html_body,
                    }
                )
                print("📤 Mailgun response:", response.status_code, response.text)

            except Exception:
                traceback.print_exc()

        return jsonify({
            "message": "QR created",
            "clickable_image": f"data:image/png;base64,{img_str}",
            "do_over_link": do_over_link
        })

    except Exception as err:
        traceback.print_exc()
        return jsonify({"error": str(err)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
