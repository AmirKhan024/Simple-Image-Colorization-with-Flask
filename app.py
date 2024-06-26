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
        image = Image.open(file).convert('L')
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return render_template('preview.html', img_str=img_str)

@app.route('/colorize', methods=['POST'])
def colorize_image_route():
    image_data = request.form['image_data']
    image_bytes = base64.b64decode(image_data)
    image = Image.open(io.BytesIO(image_bytes)).convert('L')
    image_np = np.array(image)
    colorized_image_np = colorize_image(image_np)
    colorized_image = Image.fromarray(colorized_image_np)
    image_id = save_image_to_mongo(colorized_image)
    return redirect(url_for('show_image', image_id=image_id))

@app.route('/image/<image_id>')
def show_image(image_id):
    image_data = mongo.db.images.find_one({'_id': ObjectId(image_id)})
    image = Image.open(io.BytesIO(image_data['data']))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return render_template('result.html', img_str=img_str)

def colorize_image(image_np):
    colorized_image_np = cv2.applyColorMap(image_np, cv2.COLORMAP_JET)
    return colorized_image_np

def save_image_to_mongo(image):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    img_data = buffer.getvalue()
    image_id = mongo.db.images.insert_one({'data': img_data}).inserted_id
    return image_id

if __name__ == '__main__':
    app.run(debug=True)
