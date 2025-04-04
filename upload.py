from flask import Flask, request, jsonify
import cloudinary
import cloudinary.uploader
from rembg import remove
from PIL import Image
import io
from flask_cors import CORS  
import os
import concurrent.futures  # For threading

app = Flask(__name__)
CORS(app)

# Configure Cloudinary
cloudinary.config( 
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),  
    api_key=os.getenv("CLOUDINARY_API_KEY"),  
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),  
    secure=True
)

executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)  # Run 5 tasks concurrently

# Function to remove background and upload image
def process_and_upload_image(image_data):
    try:
        image = Image.open(io.BytesIO(image_data)).convert("RGBA")
        
        # Resize large images to speed up processing
        max_size = (512, 512)  # Or even (300, 300) for testing
        image.thumbnail(max_size)


        # Remove background
        image_no_bg = remove(image)

        # Save to bytes
        output_no_bg = io.BytesIO()
        image_no_bg.save(output_no_bg, format="PNG")
        output_no_bg.seek(0)

        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(output_no_bg)
        return {"success": True, "image_url": upload_result["secure_url"]}

    except Exception as e:
        return {"success": False, "error": str(e)}

# Health Check Endpoint
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

# Upload Image with Background Removal
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Read image bytes
    image_data = file.read()

    # Process image in a separate thread
    future = executor.submit(process_and_upload_image, image_data)

    # Wait for the task to complete and get the result
    result = future.result()

    if result["success"]:
        return jsonify({"message": "Background removed", "image_url": result["image_url"]}), 200
    else:
        return jsonify({"error": result["error"]}), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, use_reloader=False, debug=False)
    
