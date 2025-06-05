
import io
import os
import qrcode
from flask import Flask, request, jsonify
from flask_cors import CORS
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.eyedrawers import SquareEyeDrawer, RoundedEyeDrawer, HorizontalBarsEyeDrawer
import requests
from email.message import EmailMessage
import smtplib
from PIL import Image

app = Flask(__name__)
CORS(app)

@app.route("/generate_qr", methods=["POST"])
def generate_qr():
    data = request.json
    form = {
        "email": data.get("Email address"),
        "url": data.get("Where should your QR Code point (Website/URL)?"),
        "fill_color": data.get("Data modules color (HEX# or Named color)"),
        "eye_color": data.get("Corner finder dots color (HEX# or Named color)"),
        "border_color": data.get("Border Color (HEX# or Named color)"),
        "center_color": data.get("Center image color (if no image uploaded; HEX# or Named color)"),
        "border_style": data.get("Border Style?"),
        "eye_style": data.get("Corner Finder Pattern Style?"),
        "discount_code": data.get("Discount code"),
        "first_name": data.get("First Name"),
        "last_name": data.get("Last Name"),
    }

    qr_url = form["url"] or "https://qrforus.com"
    fill_color = form["fill_color"] or "black"
    eye_color = form["eye_color"] or "black"

    img = qrcode.make(qr_url, image_factory=StyledPilImage, module_drawer=RoundedModuleDrawer(), 
                      color_mask=SolidFillColorMask(back_color="white", front_color=fill_color),
                      eye_drawer=SquareEyeDrawer())

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    msg = EmailMessage()
    msg["Subject"] = "Your QR for US™ code is ready to use!"
    msg["From"] = "qrforus@sandboxa061d0b883b44bc4becd4bcc81bef2.mailgun.org"
    msg["To"] = form["email"]

    msg.set_content(f"""Hi {form["first_name"]},

Your custom QR for US™ code is ready to use.

This one QR can be scanned, clicked, saved, or shared — on phones, flyers, websites, business cards, and anywhere else people connect with your story.

How to use your QR:
• Scan: Open any camera app and point it at the code.
• Click: If viewing this email on a device, just tap the code image.
• Save: Right-click (or tap+hold on mobile) to download the image as a PNG.

Thanks for using QR for US™ — we connect real-life moments to the digital world.

Have questions or want help with creative ideas? Email us at qrforus1@gmail.com

QR for US™
Scan It. Click It. Share your story.
https://qrforus.com
""")

    msg.add_attachment(buffer.read(), maintype="image", subtype="png", filename="qr.png")

    try:
        response = requests.post(
            "https://api.mailgun.net/v3/sandboxa061d0b883b44bc4becd4bcc81bef2.mailgun.org/messages",
            auth=("api", os.environ["MAILGUN_API_KEY"]),
            files=[("attachment", ("qr.png", buffer.getvalue()))],
            data={"from": msg["From"],
                  "to": [msg["To"]],
                  "subject": msg["Subject"],
                  "text": msg.get_content()})
        return jsonify({"status": "success", "mailgun_response": response.json()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    app.run(debug=True, port=10000)
