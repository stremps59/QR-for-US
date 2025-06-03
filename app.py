
import os
import base64
import io
from flask import Flask, request, jsonify
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer, SquareModuleDrawer, GappedSquareModuleDrawer
from qrcode.image.styles.colordrawers import SolidFillColorMask
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

MAILGUN_API_KEY = os.environ.get("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.environ.get("MAILGUN_DOMAIN")
FROM_EMAIL = os.environ.get("FROM_EMAIL")

# Map dropdown values to actual styles
BORDER_STYLE_MAP = {
    "Square": SquareModuleDrawer(),
    "Rounded": RoundedModuleDrawer(),
    "Circle": GappedSquareModuleDrawer()
}

CORNER_STYLE_MAP = {
    "Standard": SquareModuleDrawer(),
    "Rounded": RoundedModuleDrawer(),
    "Framed": GappedSquareModuleDrawer()
}

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    destination = data.get("destination")

    # Shape and color options
    border_style_key = data.get("border", "Square")
    corner_style_key = data.get("corner", "Standard")
    border_color = data.get("border_color", "black")
    corner_color = data.get("corner_color", "black")
    center_color = data.get("center_color", "black")
    data_color = data.get("data_color", "black")

    # Determine which shapes to use
    border_drawer = BORDER_STYLE_MAP.get(border_style_key, SquareModuleDrawer())
    corner_drawer = CORNER_STYLE_MAP.get(corner_style_key, SquareModuleDrawer())

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(destination)
    qr.make(fit=True)

    img = qr.make_image(image_factory=StyledPilImage,
                        module_drawer=border_drawer,
                        color_mask=SolidFillColorMask(
                            back_color="white",
                            front_color=data_color),
                        eye_drawer=corner_drawer)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    encoded_img = base64.b64encode(buffer.read()).decode("utf-8")

    subject = "Your Custom QR Code is Ready!"
    html_content = f"""
<p>Hi {name},</p>
<p>Your QR Code is ready:</p>
<p><img src="data:image/png;base64,{encoded_img}" alt="QR Code" /></p>
<p><a href="https://qrforus.com/do-over?id=placeholder">Click here to Do Over</a></p>
<hr>
<p><strong>How to use:</strong></p>
<ul>
  <li><strong>Scan or Click:</strong> This QR code links to the destination you provided: <a href="{destination}">{destination}</a></li>
  <li><strong>Print:</strong> Right-click and save the QR image to print or share</li>
  <li><strong>Customization:</strong> You may request up to 2 Do Overs within 24 hours</li>
</ul>
<p>This QR will be retained for 30 days. If you purchased a subscription, it will remain as long as your plan is active.</p>
<p>Questions? Contact us at <a href="mailto:support@qrforus.com">support@qrforus.com</a></p>
""".format(name=name, encoded_img=encoded_img, destination=destination)

    mailgun_url = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"
    response = requests.post(
        mailgun_url,
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": FROM_EMAIL,
            "to": [email],
            "subject": subject,
            "html": html_content
        }
    )

    return jsonify({"message": "QR code generated and email sent", "mailgun_response": response.text})

if __name__ == "__main__":
    app.run(debug=True)
