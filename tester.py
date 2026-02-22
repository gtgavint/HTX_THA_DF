from fastapi.testclient import TestClient
from main import app
from PIL import Image
import io

client = TestClient(app)
# Test case for successful image upload
def test_upload_image_success():
    img = Image.new('RGB', (150, 150), color='white')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)

    response = client.post(
        "/api/images",
        files={"file": ("test_cat.jpg", img_byte_arr, "image/jpeg")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    assert data["image_id"].startswith("img")

# Test case for unsupported file format.
def test_upload_invalid_file_format():
    file_content = b"test data"
    response = client.post(
        "/api/images",
        files={"file": ("test.xlsx", io.BytesIO(file_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Please upload only JPG or PNG files"

# Test case for incorrect ids
def test_get_image_not_found():
    response = client.get("/api/images/img1234")
    assert response.status_code == 404
    assert response.json()["detail"] == "Image not found"

# Test case for stats
def test_get_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "success_rate" in data
    assert "average_processing_time_seconds" in data
