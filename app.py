
from flask import Flask, request, render_template_string, send_file
import qrcode
import io
import uuid
from datetime import datetime, timedelta

app = Flask(__name__)
do_over_tokens = {}

def generate_qr_image(url, fg_color="black", bg_color="white"):
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fg_color, back_color=bg_color)
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io

@app.route('/create', methods=['POST'])
def create_qr():
    target_url = request.form['url']
    token = str(uuid.uuid4())[:8]
    do_over_tokens[token] = {
        "url": target_url,
        "fg": "black",
        "bg": "white",
        "remaining": 2,
        "created": datetime.utcnow()
    }
    do_over_link = f"https://qrforus.com/do-over?id={token}"
    return f"QR created. <a href='{do_over_link}'>Do Over link</a>"

@app.route('/do-over')
def do_over_form():
    token = request.args.get("id")
    if token not in do_over_tokens:
        return "Invalid or expired link", 400
    return render_template_string("""
        <form method='POST' action='/regenerate'>
            <input type='hidden' name='token' value='{{ token }}'>
            Foreground Color: <input type='text' name='fg' value='black'><br>
            Background Color: <input type='text' name='bg' value='white'><br>
            <button type='submit'>Generate New QR</button>
        </form>
    """, token=token)

@app.route('/regenerate', methods=['POST'])
def regenerate_qr():
    token = request.form['token']
    if token not in do_over_tokens:
        return "Invalid token", 400

    record = do_over_tokens[token]
    if datetime.utcnow() - record['created'] > timedelta(hours=24) or record['remaining'] <= 0:
        return "Do Over expired", 403

    fg = request.form['fg']
    bg = request.form['bg']
    record['fg'] = fg
    record['bg'] = bg
    record['remaining'] -= 1
    img_io = generate_qr_image(record['url'], fg, bg)
    return send_file(img_io, mimetype='image/png', as_attachment=True, download_name='qr_updated.png')

if __name__ == '__main__':
    app.run(debug=True)
