
import os
import io
import base64
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer, GappedSquareModuleDrawer, CircleModuleDrawer
from qrcode.image.styles.colordrawers import SolidFillColorMask
from PIL import Image, ImageColor

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return 'QR for US is Live!'

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    try:
        data = request.get_json()
        fields = data['data']['fields']

        # Fix destination URL extraction
        raw_dest = next((f['value'] for f in fields if 'qr code point' in f.get('label', '').lower()), '')
        if isinstance(raw_dest, list):
            raw_dest = raw_dest[0] if raw_dest else ''
        destination = raw_dest.strip() or "https://qrforus.com"

        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
        qr.add_data(destination)
        qr.make()

        img = qr.make_image(image_factory=StyledPilImage, color_mask=SolidFillColorMask(
            back_color=(255, 255, 255),
            front_color=(0, 0, 0)
        ), module_drawer=GappedSquareModuleDrawer())

        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)

        return send_file(img_io, mimetype='image/png')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
