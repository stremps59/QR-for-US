
import io
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer, GappedSquareModuleDrawer, CircleModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.eyedrawers import RoundedEyeDrawer, SquareEyeDrawer, HorizontalBarsEyeDrawer
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
from PIL import Image
import base64
import os

app = Flask(__name__)
CORS(app)

MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
SENDER_EMAIL = "QR for US <mailgun@" + MAILGUN_DOMAIN + ">"

@app.route("/")
def home():
    return "QR Code Generator is Live!"

@app.route("/generate_qr", methods=["POST"])
def generate_qr():
    try:
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

        print("Generating QR for", form["email"], "to", form["url"])

        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            border=4,
        )
        qr.add_data(form["url"])
        qr.make()

        # Select module drawer
        module_drawer = {
            "Rounded": RoundedModuleDrawer(),
            "Circle": CircleModuleDrawer(),
        }.get(form["border_style"], GappedSquareModuleDrawer())

        # Select eye drawer
        eye_drawer = {
            "Rounded": RoundedEyeDrawer(),
            "Framed": HorizontalBarsEyeDrawer(),
        }.get(form["eye_style"], SquareEyeDrawer())

        color_mask = SolidFillColorMask(
            back_color="white",
            front_color=form["fill_color"] or "black",
            center_color=form["center_color"] or "black",
            edge_color=form["eye_color"] or "black",
        )

        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=module_drawer,
            eye_drawer=eye_drawer,
            color_mask=color_mask,
        )

        # Save image to bytes buffer
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        # Prepare email
        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            files={"attachment": ("qr.png", buffer, "image/png")},
            data={
                "from": SENDER_EMAIL,
                "to": form["email"],
                "subject": "Your QR for US™ code is ready to use!",
                "html": f'''
                <p>Hi {form["first_name"]},</p>
                <p>Your custom QR for US™ code is ready to use.</p>
                <p><img src="cid:qr.png" alt="QR Code" style="width:200px;height:200px;" /></p>
                <p>This one QR can be scanned, clicked, saved, or shared — on phones, flyers, websites, business cards, and anywhere else people connect with your story.</p>
                <p><strong>How to use your QR:</strong><br>
                • <strong>Scan</strong>: Open any camera app and point it at the code.<br>
                • <strong>Click</strong>: If viewing this email on a device, just tap the code image.<br>
                • <strong>Save</strong>: Right-click (or tap-and-hold) to download the image as a PNG.</p>
                <p>Need to make a change? Use our <a href="https://qrforus.com/edit">Do-Over feature</a>.</p>
                <p>Thanks for using QR for US™ — we connect real-life moments to the digital world.<br>
                Have questions? Email us at qrforus1@gmail.com</p>
                <p><strong>QR for US™</strong><br>
                <a href="https://qrforus.com">Scan It. Click It. Share your story.</a></p>
                '''
            }
        )

        if response.status_code == 200:
            return jsonify({"status": "success", "message": "QR code sent via email"})
        else:
            print("Mailgun error:", response.text)
            return jsonify({"status": "error", "message": "Failed to send email"}), 500

    except Exception as e:
        print("Unexpected error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
