from flask import Flask, request, jsonify
import cloudinary
import cloudinary.uploader
from rembg import remove
from PIL import Image
import io

app = Flask(__name__)

# Configure Cloudinary (with your credentials)
cloudinary.config( 
    cloud_name = "dypjkm3ry",  
    api_key = "997438517176368",  
    api_secret = "IiJt1BxUAuOUxWkS_8b2-jdsapk",  # Replace with actual API secret
    secure=True
)

# Function to remove background
def remove_background(input_image_file):
    image = Image.open(input_image_file).convert("RGBA")
    image_no_bg = remove(image)
    
    # Save to a bytes object (in-memory) to avoid saving to disk
    output_no_bg = io.BytesIO()
    image_no_bg.save(output_no_bg, format="PNG")
    output_no_bg.seek(0)  # Rewind the BytesIO object to start reading
    return output_no_bg

# Function to upload the processed image to Cloudinary
def upload_image_to_cloudinary(image_bytes_io):
    upload_result = cloudinary.uploader.upload(image_bytes_io, public_id="user_image_no_bg")
    return upload_result["secure_url"]

# Flask route to handle image upload and background removal
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Step 1: Remove background from the uploaded image
    removed_bg_image = remove_background(file)
    
    # Step 2: Upload the image (without background) to Cloudinary
    image_url = upload_image_to_cloudinary(removed_bg_image)

    # Step 3: Return the image URL to the user
    return jsonify({"message": "Background removed", "image_url": image_url}), 200

if __name__ == '__main__':
    app.run(debug=True)
