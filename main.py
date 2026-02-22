from fastapi import FastAPI, UploadFile, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from database import init_db, save_initial_record, update_record, fetch_stats, get_all_records, get_record_by_id
from processor import run_image_pipeline
from contextlib import asynccontextmanager
import logging
import random
import string
import os
    
# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("pipeline.log")  # Save log to file
    ]
)
logger = logging.getLogger("ImagePipeline")

# Initialise database and directories on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("thumbnails", exist_ok=True)
    yield

app = FastAPI(lifespan=lifespan)

# Image upload endpoint
@app.post("/api/images")
async def upload_image(file: UploadFile, background_tasks: BackgroundTasks):
    is_valid = file.content_type in ["image/jpeg", "image/png"]
    if not is_valid:
        raise HTTPException(status_code=400, detail="Please upload only JPG or PNG files")
    random_digits = ''.join(random.choices(string.digits, k=3))
    id = f"img{random_digits}"
    path = f"uploads/{id}_{file.filename}"
    
    with open(path, "wb") as buffer:
        buffer.write(await file.read())
    
    save_initial_record(id, file.filename)
    background_tasks.add_task(background_worker, id, path, is_valid)
    
    return {"image_id": id, "status": "processing"}

# Retrieve all image data from database
@app.get("/api/images")
def list_images():
    records = get_all_records()

    response = []
    for record in records:
        id = record["id"]

        thumbnails = {}
        if record["status"] == "success":
            thumbnails = {
                "small": f"http://localhost:8000/api/images/{id}/thumbnails/small",
                "medium": f"http://localhost:8000/api/images/{id}/thumbnails/medium"
            }

        response.append({
            "status": record["status"],
            "data": {
                "image_id": id,
                "original_name": record["original_name"],
                "processed_at": record["processed_at"],
                "metadata": record.get("metadata", {}),
                "thumbnails": thumbnails,
                "error": record["error"]
            }
        })

    return response

# Retrieve specific image details using id
@app.get("/api/images/{id}")
def get_image_details(id: str):
    record = get_record_by_id(id)
    if not record:
        raise HTTPException(status_code=404, detail="Image not found")
    
    thumbnails = {}
    if record["status"] == "success":
        thumbnails = {
            "small": f"http://localhost:8000/api/images/{id}/thumbnails/small",
            "medium": f"http://localhost:8000/api/images/{id}/thumbnails/medium"
        }
    
    return {
        "status": record["status"],
        "data": {
            "image_id": record["id"],
            "original_name": record["original_name"],
            "processed_at": record["processed_at"],
            "metadata": record["metadata"],
            "thumbnails": thumbnails
        },
        "error": record["error"]
    }

# Retrieve thumbnail images, either small or medium size
@app.get("/api/images/{id}/thumbnails/{size}")
def get_thumbnail(id: str, size: str):
    if size not in ["small", "medium"]:
        raise HTTPException(status_code=400, detail="Invalid size, use either small or medium")
    
    path = f"thumbnails/{id}_{size}.jpg"
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="Thumbnail not found")

# Background worker to process images asynchronously
def background_worker(id, path, is_valid):
    if not is_valid:
        logger.warning(f"Unable to process {id}")
        update_record(id, "failed", metadata={}, error="invalid file format", duration=0)
        return

    logger.info(f"Starting processing for image_id: {id}")
    
    status, meta, err, dur = run_image_pipeline(id, path)
    
    if status == "success":
        logger.info(f"Successfully processed {id} in {dur:.2f}s")
    else:
        logger.error(f"Failed to process {id}. Error: {err}")
        
    update_record(id, status, meta, err, dur)

# Stats endpoint to provide insights on pipeline performance
@app.get("/api/stats")
def get_pipeline_stats():
    return fetch_stats()