
from flask import Flask, request, jsonify, send_file
import qrcode
import tempfile
import os
import uuid
import logging
from PIL import ImageColor

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route("/generate_qr", methods=["POST"])
def generate_qr():
    try:
        logging.info("✅ Using NEW QR generation method")
        data = request.json

        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H)
        qr.add_data(data.get("url", "https://qrforus.com"))
        qr.make(fit=True)

        fill = data.get("fill_color", "#000000")
        back = data.get("back_color", "#FFFFFF")
        fill_rgb = ImageColor.getrgb(fill)
        back_rgb = ImageColor.getrgb(back)

        img = qr.make_image(fill_color=fill_rgb, back_color=back_rgb)

        temp_file = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.png")
        img.save(temp_file)

        return send_file(temp_file, mimetype='image/png')
    except Exception as e:
        logging.exception("🔥 Top-level error caught:")
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return "QR for US is running."

if __name__ == "__main__":
    app.run(debug=True, port=10000, host="0.0.0.0")
