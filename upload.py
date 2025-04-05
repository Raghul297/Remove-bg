from flask import Flask, request, jsonify
import cloudinary
import cloudinary.uploader
from rembg import remove
from PIL import Image
import io
from flask_cors import CORS
import os
import concurrent.futures


app = Flask(__name__)
CORS(app)

# Cloudinary Config
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

SCI_FI_BG_PATH = "ChatGPT Image Apr 4, 2025, 10_35_26 PM.png"
BLUE_BG_PATH = "plain-light-blue-background-1920-x-1080-2lqx0agfbl9srxgv.jpg"

def process_and_upload_image(image_data, mode):
    try:
        image = Image.open(io.BytesIO(image_data)).convert("RGBA")
        max_size = (512, 512)
        image.thumbnail(max_size)

        image_no_bg = remove(image)

        if mode == "sci-fi":
            bg = Image.open(SCI_FI_BG_PATH).convert("RGBA")
        elif mode == "blue":
            bg = Image.open(BLUE_BG_PATH).convert("RGBA")
        else:
            bg = None

        if bg:
            bg = bg.resize(image_no_bg.size)
            image_no_bg = Image.alpha_composite(bg, image_no_bg)

        output_io = io.BytesIO()
        image_no_bg.save(output_io, format="PNG")
        output_io.seek(0)

        upload_result = cloudinary.uploader.upload(output_io)
        return {"success": True, "image_url": upload_result["secure_url"]}

    except Exception as e:
        return {"success": False, "error": str(e)}

# 🟢 NEW: Replace background with user-provided background image
@app.route("/replace-bg", methods=["POST"])
def replace_background():
    if "file" not in request.files or "bg" not in request.files:
        return jsonify({"error": "Both 'file' and 'bg' images are required"}), 400

    try:
        file = request.files["file"]
        bg = request.files["bg"]

        fg_image = Image.open(io.BytesIO(file.read())).convert("RGBA")
        bg_image = Image.open(io.BytesIO(bg.read())).convert("RGBA")

        max_size = (512, 512)
        fg_image.thumbnail(max_size)
        bg_image = bg_image.resize(fg_image.size)

        fg_no_bg = remove(fg_image)
        combined = Image.alpha_composite(bg_image, fg_no_bg)

        output_io = io.BytesIO()
        combined.save(output_io, format="PNG")
        output_io.seek(0)

        upload_result = cloudinary.uploader.upload(output_io)
        return jsonify({"message": "Background replaced", "image_url": upload_result["secure_url"]}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Health check
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    image_data = file.read()
    mode = request.form.get("mode", "remove").lower()
    if mode not in ["remove", "sci-fi", "blue"]:
        return jsonify({"error": "Invalid mode"}), 400

    future = executor.submit(process_and_upload_image, image_data, mode)
    result = future.result()

    if result["success"]:
        return jsonify({"message": f"Image processed in {mode} mode", "image_url": result["image_url"]}), 200
    else:
        return jsonify({"error": result["error"]}), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, use_reloader=False, debug=False)
