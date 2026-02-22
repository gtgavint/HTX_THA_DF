import time
import os
from PIL import Image
from PIL.ExifTags import TAGS
from transformers import BlipProcessor, BlipForConditionalGeneration

# Initialise model
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")

# Create necessary directories if they don't exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("thumbnails", exist_ok=True)

# Extract EXIF data from image
def get_exif_data(img):
    exif_data = {}
    try:
        info = img._getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                if isinstance(value, (str, int, float)):
                    exif_data[decoded] = value
    except Exception:
        return {}
    return exif_data

# Image processing pipeline
def run_image_pipeline(image_id, file_path):
    start_time = time.time()
    try:
        img = Image.open(file_path)

        img.verify()

        img = Image.open(file_path)

        exif_data = get_exif_data(img)
        
        img = img.convert('RGB')

        # Metadata extraction
        metadata = {
            "width": img.width,
            "height": img.height,
            "format": img.format.lower() if img.format else "png",
            "size_bytes": os.path.getsize(file_path),
            "exif": exif_data
        }

        # AI caption of photos
        inputs = processor(img, return_tensors="pt")
        out = model.generate(**inputs)
        metadata["caption"] = processor.decode(out[0], skip_special_tokens=True)

        # Thumbnail generation
        for size, dims in {"small": (150, 150), "medium": (300, 300)}.items():
            thumb = img.copy()
            thumb.thumbnail(dims)
            thumb.save(f"thumbnails/{image_id}_{size}.jpg")

        return "success", metadata, None, (time.time() - start_time)
    
    # Error if unable to process
    except Exception:
        return "failed", {}, "unable to process file", 0