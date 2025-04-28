import pytest
import json
import uuid
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock
from fastapi.exceptions import HTTPException
import aiofiles

from app.utility.file_services import FileHandler, GEO_JSON_DIR, IMAGE_DIR

# --- Test Constants ---

VALID_KML_CONTENT = b"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Placemark>
    <name>Test Point</name>
    <Point><coordinates>-122.0,37.0,0</coordinates></Point>
  </Placemark>
</kml>"""

EXPECTED_GEOJSON_FEATURE = {
    "type": "Feature",
    "geometry": {
        "type": "Point",
        "coordinates": [-122.0, 37.0, 0]
    },
    "properties": {
        "name": "Test Point"
    }
}

INVALID_KML_CONTENT = b"<kml><invalid structure</kml>"
NON_UTF8_KML_CONTENT = b'\xff\xfe<\x00k\\x00m\\x00l\\x00>'
VALID_GEOJSON_CONTENT = {
    "type": "FeatureCollection",
    "features": [EXPECTED_GEOJSON_FEATURE]
}
INVALID_JSON_STRING = '{"type": "FeatureCollection", "features": [}'
INVALID_GEOJSON_STRUCTURE = {"data": "not geojson"}
IMAGE_CONTENT = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR...'

# --- Mock UploadFile class ---

class MockUploadFile:
    def __init__(self, filename: str, content: bytes, content_type: str = "application/octet-stream"):
        self.filename = filename
        self.content = content
        self._file = BytesIO(content)
        self.content_type = content_type
        self.read = AsyncMock(side_effect=self._read_sync)
        self.close = AsyncMock()

    async def _read_sync(self, size: int = -1) -> bytes:
        return self._file.read(size)

    async def seek(self, offset: int, whence: int = 0) -> int:
         return self._file.seek(offset, whence)

# --- Fixture to override directories using tmp_path ---

@pytest.fixture(autouse=True)
def override_upload_dirs(tmp_path: Path, mocker):
    # Create temporary directories for GEO_JSON_DIR and IMAGE_DIR
    tmp_geo_json = tmp_path / "geo_jsons"
    tmp_images = tmp_path / "images"
    tmp_geo_json.mkdir(parents=True, exist_ok=True)
    tmp_images.mkdir(parents=True, exist_ok=True)
    # Patch the constants in your module so that all file I/O occurs in tmp_path
    mocker.patch("app.utility.file_services.GEO_JSON_DIR", tmp_geo_json)
    mocker.patch("app.utility.file_services.IMAGE_DIR", tmp_images)
    yield
    # No explicit cleanup is needed here because tmp_path is automatically removed.

# --- Dummy conversion function for tests simulating success ---
def dummy_convert(input_path: str, output_dir: str):
    """
    Dummy conversion function that writes VALID_GEOJSON_CONTENT to the expected output file.
    """
    output_file = Path(output_dir) / (Path(input_path).stem + ".geojson")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(VALID_GEOJSON_CONTENT, f, indent=4)

# --- Tests for KML Conversion ---

@pytest.mark.asyncio
async def test_convert_and_save_kml_to_geojson_success(tmp_path: Path, mocker):
    """Test successful KML to GeoJSON conversion and saving."""
    input_file = tmp_path / "input.kml"
    output_file = tmp_path / "test.geojson"
    async with aiofiles.open(input_file, "wb") as f:
        await f.write(VALID_KML_CONTENT)
    
    await FileHandler.convert_and_save_kml_to_geojson(input_file, output_file)
    
    assert await aiofiles.os.path.exists(output_file)
    async with aiofiles.open(output_file, "r", encoding="utf-8") as f:
        data = json.loads(await f.read())
    assert data["type"] == "FeatureCollection"
    feature = data["features"][0]
    assert feature["geometry"] == EXPECTED_GEOJSON_FEATURE["geometry"]
    assert feature["properties"]["name"] == EXPECTED_GEOJSON_FEATURE["properties"]["name"]

@pytest.mark.asyncio
async def test_convert_and_save_kml_non_utf8(tmp_path: Path):
    """Test conversion failure with non-UTF-8 KML content."""
    input_file = tmp_path / "non_utf8.kml"
    output_file = tmp_path / "non_utf8.geojson"
    async with aiofiles.open(input_file, "wb") as f:
        await f.write(NON_UTF8_KML_CONTENT)
    with pytest.raises(ValueError, match=r"Invalid KML structure or encoding"):
        await FileHandler.convert_and_save_kml_to_geojson(input_file, output_file)
        print("Conversion failed as expected")
    assert not await aiofiles.os.path.exists(output_file)

@pytest.mark.asyncio
async def test_convert_and_save_kml_invalid_structure(tmp_path: Path):
    """Test conversion failure with invalid KML structure."""
    input_file = tmp_path / "invalid.kml"
    output_file = tmp_path / "invalid.geojson"
    async with aiofiles.open(input_file, "wb") as f:
        await f.write(INVALID_KML_CONTENT)
    with pytest.raises(ValueError, match=r"Invalid KML structure or encoding.*"):
        await FileHandler.convert_and_save_kml_to_geojson(input_file, output_file)
    assert not await aiofiles.os.path.exists(output_file)

# @pytest.mark.asyncio
# async def test_convert_and_save_kml_os_error(tmp_path: Path, mocker):
#     """Test handling OSError during conversion by mocking shutil.move to raise OSError."""
#     output_file = tmp_path / "os_error.geojson"
#     # Patch shutil.move to raise an OSError
#     mocker.patch("shutil.move", side_effect=OSError("Disk full"))
#     mocker.patch("aiofiles.os.makedirs", return_value=None)
#     with pytest.raises(OSError, match="File operation failed during KML conversion: Disk full"):
#         await FileHandler.convert_and_save_kml_to_geojson(VALID_KML_CONTENT, output_file)
#     assert not await aiofiles.os.path.exists(output_file)

# --- Tests for _get_upload_path ---

@pytest.mark.asyncio
async def test_get_upload_path_kml():
    """Test path generation for KML files."""
    mock_file = MockUploadFile("test.kml", b"", "application/vnd.google-earth.kml+xml")
    fpath = await FileHandler._get_upload_path(mock_file)
    assert fpath.parent.name == GEO_JSON_DIR.name
    # _get_upload_path returns the original extension (".kml")
    assert fpath.suffix == ".kml"
    base_name = fpath.name[:-len(fpath.suffix)]
    uuid.UUID(base_name, version=4)

@pytest.mark.asyncio
async def test_get_upload_path_image():
    """Test path generation for image files."""
    mock_file = MockUploadFile("logo.png", b"", "image/png")
    fpath = await FileHandler._get_upload_path(mock_file)
    assert fpath.parent.name == IMAGE_DIR.name
    assert fpath.suffix == ".png"
    base_name = fpath.name[:-len(".png")]
    uuid.UUID(base_name, version=4)

@pytest.mark.asyncio
async def test_get_upload_path_no_extension():
    """Test handling files with no extension."""
    mock_file = MockUploadFile("myfile", b"")
    with pytest.raises(HTTPException, match="File has no extension"):
        await FileHandler._get_upload_path(mock_file)

# --- Tests for save_file ---

@pytest.mark.asyncio
async def test_save_file_kml_success(tmp_path: Path, mocker):
    """Test saving a KML file (triggers conversion)."""
    
    mock_upload = MockUploadFile("input.kml", VALID_KML_CONTENT, "application/vnd.google-earth.kml+xml")
    saved_path_str = await FileHandler.save_file(mock_upload)
    saved_path = Path(saved_path_str)
    assert saved_path.suffix == ".geojson"
    # The parent should be our patched directory (from override_upload_dirs) so its name will be \"geo_jsons\"
    assert saved_path.parent.name == "geo_jsons"
    assert await aiofiles.os.path.exists(saved_path)
    async with aiofiles.open(saved_path, 'r', encoding='utf-8') as f:
        data = json.loads(await f.read())
    assert data["type"] == "FeatureCollection"
    assert data["features"][0]["properties"]["name"] == "Test Point"
    await aiofiles.os.remove(saved_path)

@pytest.mark.asyncio
async def test_save_file_image_success(tmp_path: Path, mocker):
    """Test saving a non-KML file (image)."""
    mock_upload = MockUploadFile("picture.png", IMAGE_CONTENT, "image/png")
    saved_path_str = await FileHandler.save_file(mock_upload)
    saved_path = Path(saved_path_str)
    assert saved_path.suffix == ".png"
    assert saved_path.parent.name == "images"
    assert await aiofiles.os.path.exists(saved_path)
    async with aiofiles.open(saved_path, 'rb') as f:
        content = await f.read()
    assert content == IMAGE_CONTENT
    await aiofiles.os.remove(saved_path)

@pytest.mark.asyncio
async def test_save_file_empty(tmp_path: Path, mocker):
    """Test saving an empty file raises an HTTPException."""
    mock_upload = MockUploadFile("empty.txt", b"", "text/plain")
    with pytest.raises(HTTPException, match="Empty file uploaded"):
        await FileHandler.save_file(mock_upload)

# --- Tests for load_geojson_content ---

@pytest.mark.asyncio
async def test_load_geojson_content_success(tmp_path: Path):
    """Test loading valid GeoJSON content."""
    geojson_file = tmp_path / "valid.geojson"
    async with aiofiles.open(geojson_file, "w", encoding="utf-8") as f:
        await f.write(json.dumps(VALID_GEOJSON_CONTENT))
    data = await FileHandler.load_geojson_content(geojson_file)
    assert data == VALID_GEOJSON_CONTENT
    await aiofiles.os.remove(geojson_file)

@pytest.mark.asyncio
async def test_load_geojson_content_not_found(tmp_path: Path):
    """Test loading a non-existent GeoJSON file."""
    non_existent_file = tmp_path / "not_here.geojson"
    with pytest.raises(HTTPException, match="GeoJSON file not found"):
        await FileHandler.load_geojson_content(non_existent_file)

@pytest.mark.asyncio
async def test_load_geojson_content_invalid_json(tmp_path: Path):
    """Test loading a file with invalid JSON."""
    invalid_file = tmp_path / "invalid.json"
    async with aiofiles.open(invalid_file, "w", encoding="utf-8") as f:
        await f.write(INVALID_JSON_STRING)
    with pytest.raises(HTTPException, match="Could not parse GeoJSON"):
        await FileHandler.load_geojson_content(invalid_file)
    await aiofiles.os.remove(invalid_file)

@pytest.mark.asyncio
async def test_load_geojson_content_invalid_structure(tmp_path: Path):
    """Test loading JSON that is not valid GeoJSON structure."""
    invalid_structure_file = tmp_path / "invalid_structure.json"
    async with aiofiles.open(invalid_structure_file, "w", encoding="utf-8") as f:
        await f.write(json.dumps(INVALID_GEOJSON_STRUCTURE))
    with pytest.raises(HTTPException, match="Invalid GeoJSON structure"):
        await FileHandler.load_geojson_content(invalid_structure_file)
    await aiofiles.os.remove(invalid_structure_file)

# --- Tests for delete_file and file_exists ---

@pytest.mark.asyncio
async def test_delete_file_success(tmp_path: Path):
    """Test deleting an existing file."""
    file_to_delete = tmp_path / "delete_me.txt"
    async with aiofiles.open(file_to_delete, "w") as f:
        await f.write("content")
    assert await aiofiles.os.path.exists(file_to_delete)
    await FileHandler.delete_file(file_to_delete)
    assert not await aiofiles.os.path.exists(file_to_delete)

@pytest.mark.asyncio
async def test_delete_file_non_existent(tmp_path: Path):
    """Test deleting a non-existent file (should not raise error)."""
    non_existent_file = tmp_path / "not_here.txt"
    await FileHandler.delete_file(non_existent_file)
    assert not await aiofiles.os.path.exists(non_existent_file)

@pytest.mark.asyncio
async def test_file_exists(tmp_path: Path):
    """Test the file_exists method."""
    existing_file = tmp_path / "exists.txt"
    non_existent_file = tmp_path / "not_exists.txt"
    async with aiofiles.open(existing_file, "w") as f:
        await f.write("content")
    assert await FileHandler.file_exists(existing_file) is True
    assert await FileHandler.file_exists(non_existent_file) is False
    await aiofiles.os.remove(existing_file)

# --- Test for overwrite_file ---
@pytest.mark.asyncio
async def test_overwrite_file_success(tmp_path: Path):
    """Test successfully overwriting an existing file using a temporary file and atomic move."""
    target_file = tmp_path / "overwrite_me.txt"
    async with aiofiles.open(target_file, "w") as f:
        await f.write("old content")
    
    new_content = b"new content"
    mock_upload = MockUploadFile("new_file.txt", new_content, "application/geo+json")
    
    await FileHandler.overwrite_file(mock_upload, target_file)
    
    assert await aiofiles.os.path.exists(target_file)
    async with aiofiles.open(target_file, "rb") as f:
        content = await f.read()
    assert content == new_content
    await aiofiles.os.remove(target_file)
