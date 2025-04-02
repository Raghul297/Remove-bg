from flask import Flask, request, jsonify
import cloudinary
import cloudinary.uploader
from rembg import remove
from PIL import Image
import io
from flask_cors import CORS  # Enables CORS for frontend requests
import os

app = Flask(__name__)
CORS(app)  # Allow requests from any frontend (adjust if needed)

# Configure Cloudinary
cloudinary.config( 
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),  
    api_key = os.getenv("CLOUDINARY_API_KEY"),  
    api_secret = os.getenv("CLOUDINARY_API_SECRET"),  
    secure=True
)

# Function to remove background
def remove_background(input_image_file):
    image = Image.open(input_image_file).convert("RGBA")
    image_no_bg = remove(image)
    
    # Save to a bytes object (in-memory)
    output_no_bg = io.BytesIO()
    image_no_bg.save(output_no_bg, format="PNG")
    output_no_bg.seek(0)
    return output_no_bg

# Function to upload the processed image to Cloudinary
def upload_image_to_cloudinary(image_bytes_io):
    upload_result = cloudinary.uploader.upload(image_bytes_io, public_id="user_image_no_bg")
    return upload_result["secure_url"]

# Health Check Endpoint (Useful for Choreo)
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

# Flask route to handle image upload and background removal
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Remove background
    removed_bg_image = remove_background(file)
    
    # Upload the image (without background) to Cloudinary
    image_url = upload_image_to_cloudinary(removed_bg_image)

    # Return the image URL to the user
    return jsonify({"message": "Background removed", "image_url": image_url}), 200

if __name__ == '__main__':
    # Run on Choreo-compatible settings
    port = int(os.getenv("PORT", 8080))  # Default port for Choreo
    app.run(host="0.0.0.0", port=port, debug=True)
