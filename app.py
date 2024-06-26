from flask import Flask, request, render_template, redirect, url_for
from flask_pymongo import PyMongo
from PIL import Image
import cv2
import numpy as np
import io
import base64
from bson.objectid import ObjectId

app = Flask(__name__)
app.config.from_object('config')
mongo = PyMongo(app)

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return redirect(request.url)
    file = request.files['image']
    if file.filename == '':
        return redirect(request.url)
    if file:
        image = Image.open(file)
        grayscale_image = image.convert('L')
        buffer = io.BytesIO()
        grayscale_image.save(buffer, format="PNG")
        buffer_value = buffer.getvalue()
        img_str = base64.b64encode(buffer_value)
        img_str_decoded = img_str.decode()
        return render_template('preview.html', img_str=img_str_decoded)

@app.route('/colorize', methods=['POST'])
def colorize_image_route():
    image_data = request.form['image_data']
    image_bytes = base64.b64decode(image_data)
    image_buffer = io.BytesIO(image_bytes)
    image = Image.open(image_buffer)
    grayscale_image = image.convert('L')
    image_np = np.array(grayscale_image)
    colorized_image_np = colorize_image(image_np)
    colorized_image = Image.fromarray(colorized_image_np)
    image_id = save_image_to_mongo(colorized_image)
    return redirect(url_for('show_image', image_id=image_id))

@app.route('/image/<image_id>')
def show_image(image_id):
    object_id = ObjectId(image_id)
    image_data = mongo.db.images.find_one({'_id': object_id})
    image_bytes = image_data['data']
    image_buffer = io.BytesIO(image_bytes)
    image = Image.open(image_buffer)
    output_buffer = io.BytesIO()
    image.save(output_buffer, format="PNG")
    output_value = output_buffer.getvalue()
    img_str = base64.b64encode(output_value)
    img_str_decoded = img_str.decode()
    return render_template('result.html', img_str=img_str_decoded)

def colorize_image(image_np):
    image_8bit = cv2.normalize(image_np, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    colormap = cv2.COLORMAP_JET
    colorized_image_np = cv2.applyColorMap(image_8bit, colormap)
    return colorized_image_np

def save_image_to_mongo(image):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    img_data = buffer.getvalue()
    result = mongo.db.images.insert_one({'data': img_data})
    image_id = result.inserted_id
    return image_id

def validate_image(file):
    if file and allowed_file(file.filename):
        return True
    return False

def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_image_format(filename):
    return filename.rsplit('.', 1)[1].lower()

def create_image_buffer(image, format):
    buffer = io.BytesIO()
    image.save(buffer, format=format.upper())
    return buffer

def encode_image(buffer):
    buffer_value = buffer.getvalue()
    encoded_image = base64.b64encode(buffer_value)
    return encoded_image.decode()

def decode_image_data(image_data):
    image_bytes = base64.b64decode(image_data)
    image_buffer = io.BytesIO(image_bytes)
    return Image.open(image_buffer)

def normalize_image(image_np):
    return cv2.normalize(image_np, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

def apply_colormap(image_np, colormap=cv2.COLORMAP_JET):
    return cv2.applyColorMap(image_np, colormap)

if __name__ == '__main__':
    app.run(debug=True)