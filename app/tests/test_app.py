#!/usr/bin/env python3
import os
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Adjust the imports as needed for your project structure.
from app.app import app
from app.database import Base, get_session

# Override the database dependency with a SQLite test database.
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_session():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_session] = override_get_session
client = TestClient(app)

# Fixture to create/drop tables before each test
@pytest.fixture(scope="function", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# --- Override Upload Directories Fixture ---
@pytest.fixture(autouse=True)
def override_upload_dirs(tmp_path, mocker):
    # Create temporary directories for file uploads
    tmp_geo_json = tmp_path / "geo_jsons"
    tmp_images = tmp_path / "images"
    tmp_geo_json.mkdir(parents=True, exist_ok=True)
    tmp_images.mkdir(parents=True, exist_ok=True)
    # Patch the global constants so that any file I/O uses these directories
    mocker.patch("app.utility.file_services.GEO_JSON_DIR", tmp_geo_json)
    mocker.patch("app.utility.file_services.IMAGE_DIR", tmp_images)
    yield
    # The tmp_path fixture will clean up automatically

# --------------------------
# Institution Endpoint Tests
# --------------------------

def test_create_institution_success():
    payload = {
        "name": "Ahmadu Bello University",
        "country": "Nigeria",
        "address": "Zaria, Kaduna",
        "chapter_name": "ABU Mapping Team",
        "OSM_mapping": 9,
        "contributor_full_name": "Fatima Sani",
        "contributor_email": "fatima@abu.edu.ng",
        "contributor_phone_number": "+2348039990000",
        "role_in_chapter": "Member"
    }
    res = client.post("/api/v1/institution", json=payload)
    assert res.status_code == 201
    assert res.json()["name"] == payload["name"]

def test_get_institution_success():
    payload = {
        "name": "UNILAG",
        "country": "Nigeria",
        "address": "Lagos",
        "chapter_name": "UNILAG Mappers",
        "OSM_mapping": 3,
        "contributor_full_name": "John Doe",
        "contributor_email": "john@unilag.edu.ng",
        "contributor_phone_number": "+2348012345678",
        "role_in_chapter": "Leader"
    }
    res = client.post("/api/v1/institution", json=payload)
    institution_id = res.json()["id"]
    get_res = client.get(f"/api/v1/institution/{institution_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == payload["name"]

def test_duplicate_institution_error():
    payload = {
        "name": "UNIBEN",
        "country": "Nigeria",
        "address": "Benin City",
        "chapter_name": "Geo Club",
        "OSM_mapping": 5,
        "contributor_full_name": "Tunde Bello",
        "contributor_email": "tunde@uniben.edu.ng",
        "contributor_phone_number": "+2348012345678",
        "role_in_chapter": "Coordinator"
    }
    res1 = client.post("/api/v1/institution", json=payload)
    assert res1.status_code == 201
    res2 = client.post("/api/v1/institution", json=payload)
    assert res2.status_code == 400
    assert res2.json()["detail"] == "Institution already exists"

def test_invalid_data_structure():
    res = client.post("/api/v1/institution", json={"wrong_field": "value"})
    assert res.status_code == 422

def test_missing_required_fields():
    res = client.post("/api/v1/institution", json={"name": "Missing Fields Uni"})
    assert res.status_code == 422

# Helper function for file tests: create an institution and return its ID.
def create_test_institution():
    payload = {
        "name": "Test Uni",
        "country": "Nigeria",
        "address": "Test Location",
        "chapter_name": "Test Chapter",
        "OSM_mapping": 1,
        "contributor_full_name": "Test User",
        "contributor_email": "test@uni.ng",
        "contributor_phone_number": "+23412345678",
        "role_in_chapter": "Member"
    }
    res = client.post("/api/v1/institution", json=payload)
    return res.json()["id"]

# --------------------------
# File Endpoint Tests
# --------------------------

# For file tests, we create temporary files locally.
def test_upload_files():
    institution_id = create_test_institution()
    geo_file = "geo_test.geojson"
    img_file = "img_test.png"

    # Create a dummy GeoJSON file (we assume an empty FeatureCollection)
    with open(geo_file, "w") as f:
        json.dump({"type": "FeatureCollection", "features": []}, f)
    # Create a dummy image file
    with open(img_file, "wb") as f:
        f.write(os.urandom(1024))

    files = [
        ("files", (geo_file, open(geo_file, "rb"), "application/geo+json")),
        ("files", (img_file, open(img_file, "rb"), "image/png"))
    ]
    res = client.post("/api/v1/files/", data={"institution_id": institution_id}, files=files)
    assert res.status_code == 201
    data = res.json()
    # Check that one geo file and one image file are returned
    assert len(data["geo_files"]) == 1
    assert len(data["image_files"]) == 1

    os.remove(geo_file)
    os.remove(img_file)

def test_get_geo_file():
    institution_id = create_test_institution()
    geo_file = "get_test.geojson"

    with open(geo_file, "w") as f:
        json.dump({"type": "FeatureCollection", "features": []}, f)

    files = [("files", (geo_file, open(geo_file, "rb"), "application/geo+json"))]
    upload = client.post("/api/v1/files/", data={"institution_id": institution_id}, files=files)
    file_name = upload.json()["geo_files"][0]["name"]

    res = client.get(f"/api/v1/files/geo/{file_name}?file_type=geo")
    assert res.status_code == 200
    assert res.json()["type"] == "FeatureCollection"

    os.remove(geo_file)

def test_update_file():
    institution_id = create_test_institution()
    orig = "update_orig.geojson"
    new = "update_new.geojson"

    with open(orig, "w") as f:
        json.dump({"type": "FeatureCollection", "features": []}, f)

    files = [("files", (orig, open(orig, "rb"), "application/geo+json"))]
    upload = client.post("/api/v1/files/", data={"institution_id": institution_id}, files=files)
    file_name = upload.json()["geo_files"][0]["name"]

    # Create new content for update
    with open(new, "w") as f:
        json.dump({"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [1, 2]}, "properties": {"name": "Updated Point"}}]}, f)

    res = client.put(
        f"/api/v1/files/geo/{file_name}",
        files={"file": (new, open(new, "rb"), "application/geo+json")}
    )
    assert res.status_code == 200
    # Check that the file name remains unchanged
    assert res.json()["name"] == file_name

    os.remove(orig)
    os.remove(new)

def test_delete_file():
    institution_id = create_test_institution()
    geo_file = "del_test.geojson"

    with open(geo_file, "w") as f:
        json.dump({"type": "FeatureCollection", "features": []}, f)

    files = [("files", (geo_file, open(geo_file, "rb"), "application/geo+json"))]
    upload = client.post("/api/v1/files/", data={"institution_id": institution_id}, files=files)
    file_name = upload.json()["geo_files"][0]["name"]

    res = client.delete(f"/api/v1/files/geo/{file_name}?file_type=geo")
    assert res.status_code == 200
    assert res.json()['msg'] == f"{file_name} deleted successfully"

    os.remove(geo_file)


def test_upload_empty_file():
    institution_id = create_test_institution()
    empty_filename = "empty.kml"
    # Create an empty file
    with open(empty_filename, "w") as f:
        f.write("")
    files = [("files", (empty_filename, open(empty_filename, "rb"), "application/vnd.google-earth.kml+xml"))]
    res = client.post("/api/v1/files/", data={"institution_id": institution_id}, files=files)
    os.remove(empty_filename)
    assert res.status_code == 400
    assert "Empty file uploaded" in res.json()["detail"]


def test_upload_unsupported_file_type():
    institution_id = create_test_institution()
    # Create a dummy file with an unsupported MIME type
    unsupported_filename = "unsupported.docx"
    with open(unsupported_filename, "w", encoding="utf-8") as f:
        f.write("This is not supported.")
    files = [("files", (unsupported_filename, open(unsupported_filename, "rb"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))]
    res = client.post("/api/v1/files/", data={"institution_id": institution_id}, files=files)
    os.remove(unsupported_filename)
    assert res.status_code == 400
    assert "Invalid file type" in res.json()["detail"]

def test_file_upload_kml_conversion(tmp_path):
    institution_id = create_test_institution()
    kml_filename = "test_conversion.kml"
    # Write a valid KML file (the endpoint should convert it)
    kml_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
        '  <Placemark>\n'
        '    <name>Test Point</name>\n'
        '    <Point><coordinates>-122.0,37.0,0</coordinates></Point>\n'
        '  </Placemark>\n'
        '</kml>'
    )
    with open(kml_filename, "w", encoding="utf-8") as f:
        f.write(kml_content)
    
    files = [("files", (kml_filename, open(kml_filename, "rb"), "application/vnd.google-earth.kml+xml"))]
    res = client.post("/api/v1/files/", data={"institution_id": institution_id}, files=files)
    os.remove(kml_filename)
    assert res.status_code == 201, res.text
    data = res.json()
    # Expect one geo file (with .geojson extension)
    assert len(data["geo_files"]) == 1
    geo_record = data["geo_files"][0]
    assert geo_record["name"].endswith(".geojson")
    # Optionally, you can GET the file and verify its content is valid GeoJSON.
    file_name = geo_record["name"]
    get_res = client.get(f"/api/v1/files/geo/{file_name}?file_type=geo")
    assert get_res.status_code == 200
    geojson_data = get_res.json()
    assert geojson_data.get("type") == "FeatureCollection"

# Error Handling for Missing File on Disk
def test_get_file_missing_on_disk(tmp_path):
    institution_id = create_test_institution()
    # First, upload a valid image file
    img_filename = "test_image.png"
    with open(img_filename, "wb") as f:
        f.write(os.urandom(1024))
    
    files = [("files", (img_filename, open(img_filename, "rb"), "image/png"))]
    upload_res = client.post("/api/v1/files/", data={"institution_id": institution_id}, files=files)
    os.remove(img_filename)
    assert upload_res.status_code == 201, upload_res.text
    image_record = upload_res.json()["image_files"][0]
    file_name = image_record["name"]

    # Manually delete the file from disk to simulate missing file
    from app.utility.file_services import IMAGE_DIR
    file_path = Path(IMAGE_DIR) / file_name
    if file_path.exists():
        os.remove(file_path)

    # Now try to retrieve the file via GET endpoint; it should raise an error
    get_res = client.get(f"/api/v1/files/image/{file_name}?file_type=image")
    assert get_res.status_code == 404
    # Optionally check error detail
    assert "missing in filesystem" in get_res.json()["detail"].lower()


def test_update_institution_success():
    # Create an institution first
    payload = {
        "name": "University of Ibadan",
        "country": "Nigeria",
        "address": "Ibadan, Oyo",
        "chapter_name": "UI Mapping Team",
        "OSM_mapping": 7,
        "contributor_full_name": "Adeola Akin",
        "contributor_email": "adeola@ui.edu.ng",
        "contributor_phone_number": "+2348023456789",
        "role_in_chapter": "Coordinator"
    }
    res = client.post("/api/v1/institution", json=payload)
    assert res.status_code == 201
    institution_id = res.json()["id"]

    # Update the institution
    updated_payload = {
        "name": "University of Ibadan",
        "country": "Nigeria",
        "address": "Updated Address, Ibadan",
        "chapter_name": "UI Mapping Team Updated",
        "OSM_mapping": 10,
        "contributor_full_name": "Adeola Akin Updated",
        "contributor_email": "adeola.updated@ui.edu.ng",
        "contributor_phone_number": "+2348023456789",
        "role_in_chapter": "Leader"
    }
    update_res = client.put(f"/api/v1/institution/{institution_id}", json=updated_payload)
    assert update_res.status_code == 200
    assert update_res.json()["address"] == updated_payload["address"]
    assert update_res.json()["chapter_name"] == updated_payload["chapter_name"]

def test_delete_institution_success():
    # Create an institution first
    payload = {
        "name": "Obafemi Awolowo University",
        "country": "Nigeria",
        "address": "Ile-Ife, Osun",
        "chapter_name": "OAU Mapping Team",
        "OSM_mapping": 6,
        "contributor_full_name": "Bola Ade",
        "contributor_email": "bola@oau.edu.ng",
        "contributor_phone_number": "+2348034567890",
        "role_in_chapter": "Member"
    }
    res = client.post("/api/v1/institution", json=payload)
    assert res.status_code == 201
    institution_id = res.json()["id"]

    # Delete the institution
    delete_res = client.delete(f"/api/v1/institution/{institution_id}")
    assert delete_res.status_code == 200
    assert delete_res.json()["msg"] == "Institution deleted successfully"

    # Verify the institution no longer exists
    get_res = client.get(f"/api/v1/institution/{institution_id}")
    assert get_res.status_code == 404
    assert "not found" in get_res.json()["detail"].lower()
    