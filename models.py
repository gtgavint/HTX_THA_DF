from pydantic import BaseModel
from typing import Optional, Dict

class ImageMetadata(BaseModel):
    width: int
    height: int
    format: str
    size_bytes: int
    caption: Optional[str] = None

class ImageRecord(BaseModel):
    image_id: str
    original_name: str
    status: str
    processed_at: Optional[str] = None
    metadata: Dict = {}
    error: Optional[str] = None