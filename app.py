import os
import io
import uuid
import base64
import sys
import qrcode_styled as qrcode
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

# Advanced styling modules
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import SquareModuleDrawer, RoundedModuleDrawer, CircleModuleDrawer
from qrcode.image.styles.eyedrawers import SquareEyeDrawer, RoundedEyeDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask

app = Flask(__name__)
CORS(app)

MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY", "")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN", "")
MAILGUN_FROM = os.getenv("MAILGUN_FROM", f"mailgun@{MAILGUN_DOMAIN}")

@app.route("/")
def home():
    return "QR for US backend is running"

@app.route("/generate_qr", methods=["POST"])
def generate_qr():
    try:
        data = request.get_json(force=True) or {}
        fields = data.get("data", {}).get("fields", [])

        def get_field(label, default=""):
            for field in fields:
                if isinstance(field, dict) and field.get("label", "").strip().lower() == label.strip().lower():
                    return field.get("value", default)
            return default

        first_name = get_field("First Name", "")
        email = get_field("Email address", "")
        destination = get_field("Where should your QR Code point (Website/URL)?", "https://qrforus.com")

        border_style = get_field("Border Style?", "Square").lower()
        corner_style = get_field("Corner Finder Pattern Style?", "Standard").lower()
        border_color = get_field("Border Color (HEX# or Named color)", "black")
        dot_color = get_field("Corner finder dots color (HEX# or Named color)", "black")
        center_color = get_field("Center image color (if no image uploaded; HEX# or Named color)", "black")
        data_color = get_field("Data modules color (HEX# or Named color)", "black")

        print(f"Color Fields => Data: {data_color}, Border: {border_color}, Dots: {dot_color}, Center: {center_color}")
        print(f"Style Fields => Border: {border_style}, Eye: {corner_style}")

        module_drawer = {
            "square": SquareModuleDrawer(),
            "rounded": RoundedModuleDrawer(),
            "circle": CircleModuleDrawer()
        }.get(border_style, SquareModuleDrawer())

        eye_drawer = {
            "standard": SquareEyeDrawer(),
            "rounded": RoundedEyeDrawer(),
        }.get(corner_style, SquareEyeDrawer())

        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
        qr.add_data(destination)
        qr.make(fit=True)

        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=module_drawer,
            eye_drawer=eye_drawer,
            color_mask=SolidFillColorMask(back_color="white", front_color=data_color)
        ).convert("RGB")

        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

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
        <p><strong>QR for US™<br>"""

        return jsonify({
            "status": "success",
            "email": email,
            "image": img_base64,
            "html": html_body
        }), 200

    except Exception as e:
        sys.stderr.write(f"[QR-ERROR] {e}
")
        sys.stderr.flush()
        return jsonify({"status": "error", "message": str(e)}), 500
