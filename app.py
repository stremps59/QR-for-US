
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
        fields = {field['label'].strip().lower(): field['value'] for field in data.get("data", {}).get("fields", [])}

        name = fields.get("first name", "QR User")
        email = fields.get("email address")
        destination = fields.get("where should your qr code point (website/url)")
        qr_type = fields.get("what type of qr would you like?", ["standard"])
        if isinstance(qr_type, list):
            qr_type = qr_type[0]
        else:
            qr_type = "standard"
        color = fields.get("data modules color (hex# or named color)", "black").strip()

        # Generate QR code
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

        if MAILGUN_API_KEY and MAILGUN_DOMAIN and FROM_EMAIL and email:
            try:
                html_body = f'''
                <p>Hi {name},</p>
                <p>Your custom QR for US™ code is ready to use.</p>
                <p><img src="data:image/png;base64,{img_str}" alt="QR Code" /></p>
                <p>This one QR can be scanned, clicked, saved, or shared — on phones, flyers, websites, business cards, and anywhere else people connect with your story.</p>
                <p><strong>How to use your QR:</strong></p>
                <ul>
                  <li><strong>Scan:</strong> Open any camera app and point it at the code.</li>
                  <li><strong>Click:</strong> If viewing this email on a device, just tap the code image.</li>
                  <li><strong>Save:</strong> Right-click (or tap+hold on mobile) to download the image as a PNG.</li>
                </ul>
                <p><a href="{do_over_link}">Need to make a change? Use our “Do Over” feature here.</a></p>
                <p>Thanks for using QR for US™ — we connect real-life moments to the digital world.</p>
                <p>Have questions? Email us at qrforus1@gmail.com</p>
                <p>--<br/>QR for US™<br/>Scan it. Click it. Share your story.<br/><a href="https://qrforus.com">https://qrforus.com</a></p>
                '''

                text_body = f'''
Hi {name},

Your QR for US(TM) code is ready to use!
Attached is your custom QR code as a PNG image.

This one QR can be scanned, clicked, saved, or shared — on phones, flyers, websites, business cards, and anywhere else people connect with your story.

How to use your QR:
1. Scan: Open any camera app and point it at the code.
2. Click: Insert the image in any doc or email and hyperlink it.
3. Save: Right-click or tap+hold to download the PNG image.

Need to make a change? Use our "Do Over" link:
{do_over_link}

Thanks for using QR for US(TM) — we connect real-life moments to the digital world.

Have questions or creative ideas? Email us at qrforus1@gmail.com

--
QR for US(TM)
Scan it. Click it. Share your story.
https://qrforus.com
                '''

                response = requests.post(
                    f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
                    auth=("api", MAILGUN_API_KEY),
                    data={
                        "from": FROM_EMAIL,
                        "to": email,
                        "subject": "Your QR for US™ code is ready to use!",
                        "html": html_body,
                        "text": text_body
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
