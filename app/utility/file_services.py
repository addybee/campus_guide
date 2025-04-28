#!/usr/bin/env python3
"""
This module provides utility functions for handling file operations, including
saving, deleting, and converting files. It supports asynchronous operations
and handles GeoJSON and image files.
"""

import uuid
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Any
from xml.parsers.expat import ExpatError

import aiofiles
import aiofiles.os
import anyio
from fastapi import UploadFile, HTTPException

import kml2geojson.main
from app import GEO_MIME_TYPES

logger = logging.getLogger(__name__)

# Define base directories for file storage
BASE_STATIC_DIR = Path("app/static")
GEO_JSON_DIR = BASE_STATIC_DIR / "geo_jsons"
IMAGE_DIR = BASE_STATIC_DIR / "images"


class FileHandler:
    """
    A utility class for handling file operations, including saving, deleting,
    and converting files.
    """

    @staticmethod
    async def convert_and_save_kml_to_geojson(input_filepath: Path, output_filepath: Path) -> None:
        """
        Converts a KML file to GeoJSON and saves it to the specified path.

        Args:
            input_filepath (Path): The path to the input KML file.
            output_filepath (Path): The path to save the converted GeoJSON file.

        Raises:
            ValueError: If the KML file is invalid or conversion fails.
        """
        try:
            await aiofiles.os.makedirs(output_filepath.parent, exist_ok=True)

            try:
                result = kml2geojson.main.convert(str(input_filepath))
            except ExpatError as e:
                logger.error(f"Error parsing KML file: {e}")
                raise ValueError("Invalid KML structure or encoding") from e
            except Exception as e:
                logger.error(f"Error converting KML to GeoJSON: {e}")
                raise ValueError("KML to GeoJSON conversion failed") from e

            geojson_dict = result[0] if isinstance(result, list) else result[1]

            if not geojson_dict:
                logger.error(f"Invalid KML structure or encoding: {input_filepath}")
                raise ValueError("Invalid KML structure or encoding")

            async with aiofiles.open(output_filepath, "w", encoding="utf-8") as f:
                await f.write(json.dumps(geojson_dict))

            if not await aiofiles.os.path.exists(output_filepath):
                logger.error(f"GeoJSON file not created: {output_filepath}")
                raise ValueError("KML to GeoJSON conversion failed, file not created")

            logger.info(f"Successfully converted and saved GeoJSON to: {output_filepath}")

        except Exception as e:
            logger.error(f"Error during KML conversion/saving process: {e}")
            raise
        finally:
            if input_filepath and await aiofiles.os.path.exists(input_filepath):
                try:
                    await aiofiles.os.remove(input_filepath)
                except Exception as cleanup_e:
                    logger.warning(f"Failed to clean up temp KML file: {cleanup_e}")

    @staticmethod
    async def _get_upload_path(uploaded_file: UploadFile) -> Path:
        """
        Determines the upload path for a file based on its type.

        Args:
            uploaded_file (UploadFile): The uploaded file.

        Returns:
            Path: The path where the file should be saved.

        Raises:
            HTTPException: If the file has no extension.
        """
        file_extension = Path(uploaded_file.filename).suffix
        if not file_extension:
            raise HTTPException(status_code=400, detail="File has no extension")

        new_filename = f"{uuid.uuid4()}{file_extension}"
        upload_dir = GEO_JSON_DIR if uploaded_file.content_type in GEO_MIME_TYPES else IMAGE_DIR
        await aiofiles.os.makedirs(upload_dir, exist_ok=True)
        return upload_dir / new_filename

    @staticmethod
    async def save_file(uploaded_file: UploadFile) -> Path:
        """
        Saves an uploaded file asynchronously. Converts KML to GeoJSON if needed.

        Args:
            uploaded_file (UploadFile): The file uploaded via FastAPI.

        Returns:
            Path: The path of the saved file.

        Raises:
            HTTPException: If the file is empty or errors occur during saving.
        """
        try:
            file_path_obj = await FileHandler._get_upload_path(uploaded_file)

            content = await uploaded_file.read()
            if not content:
                raise HTTPException(status_code=400, detail="Empty file uploaded")

            async with aiofiles.open(file_path_obj, "wb") as buffer:
                await buffer.write(content)

            if Path(uploaded_file.filename).suffix.lower() == '.kml':
                output_filepath = file_path_obj.with_suffix(".geojson")
                await FileHandler.convert_and_save_kml_to_geojson(file_path_obj, output_filepath)
                file_path_obj = output_filepath

            logger.info(f"File saved successfully to: {file_path_obj}")
            return file_path_obj

        except HTTPException:
            raise
        except ValueError as e:
            logger.error(f"ValueError during file processing: {e}")
            raise HTTPException(status_code=400, detail=f"Error processing KML file: {e}")
        except OSError as e:
            logger.error(f"OSError during file saving: {e}")
            raise HTTPException(status_code=500, detail=f"Could not save file on server: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error saving file {uploaded_file.filename}: {e}")
            raise HTTPException(status_code=500, detail="An internal error occurred during file saving.")
        finally:
            await uploaded_file.close()

    @staticmethod
    async def load_geojson_content(file_path: Path) -> Dict[str, Any]:
        """
        Loads and returns the content of a GeoJSON file asynchronously.

        Args:
            file_path (Path): The path object for the GeoJSON file.

        Returns:
            Dict[str, Any]: The parsed GeoJSON content.

        Raises:
            HTTPException: If the file is missing, invalid, or parsing fails.
        """
        if not await aiofiles.os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="GeoJSON file not found")
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
                content_string = await file.read()
                parsed_data = json.loads(content_string)
                if not isinstance(parsed_data, dict) or 'type' not in parsed_data:
                    raise ValueError("Invalid GeoJSON structure: Missing 'type' key or not a dictionary.")
                return parsed_data
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="GeoJSON file not found")
        except json.JSONDecodeError:
            logger.warning(f"Could not parse JSON in file: {file_path}")
            raise HTTPException(status_code=400, detail="Could not parse GeoJSON file content")
        except ValueError as e:
            logger.warning(f"Invalid GeoJSON content in {file_path}: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error loading GeoJSON {file_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Error loading GeoJSON file: {str(e)}")

    @staticmethod
    async def delete_file(file_path: Path) -> None:
        """
        Deletes a file asynchronously from the filesystem if it exists.

        Args:
            file_path (Path): The path object of the file to delete.

        Raises:
            HTTPException: If the file cannot be deleted.
        """
        try:
            if await aiofiles.os.path.exists(file_path):
                await aiofiles.os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
            else:
                logger.warning(f"Attempted to delete non-existent file: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

    @staticmethod
    async def file_exists(file_path: Path) -> bool:
        """
        Checks asynchronously if a file exists at the given path.

        Args:
            file_path (Path): The path object to check.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        return await aiofiles.os.path.exists(file_path)

    @staticmethod
    async def overwrite_file(file: UploadFile, target_path: Path) -> None:
        """
        Safely overwrites a file asynchronously using a temporary file and atomic move.
        Converts KML files to GeoJSON before saving.

        Args:
            file (UploadFile): The new file content.
            target_path (Path): The path object of the file to be overwritten.

        Raises:
            HTTPException: If the file cannot be overwritten.
        """
        temp_file_path: Path | None = None
        try:
            # Create a temporary file path
            temp_filename = f".{uuid.uuid4()}.tmp"
            temp_file_path = target_path.parent / temp_filename

            # Write the uploaded file content to the temporary file
            async with aiofiles.open(temp_file_path, "wb") as tmp:
                while True:
                    chunk = await file.read(1024 * 1024)  # Read in chunks of 1MB
                    if not chunk:
                        break
                    await tmp.write(chunk)

            # Check if the file is a KML file and convert it to GeoJSON
            if Path(file.filename).suffix.lower() == '.kml':
                output_filepath = temp_file_path.with_suffix(".geojson")
                await FileHandler.convert_and_save_kml_to_geojson(temp_file_path, output_filepath)
                temp_file_path = output_filepath  # Update the temp file path to the GeoJSON file

            # Atomically move the temporary file to the target path
            await anyio.to_thread.run_sync(shutil.move, str(temp_file_path), str(target_path))
            logger.info(f"Successfully overwrote file: {target_path}")

        except Exception as e:
            logger.error(f"Failed to overwrite file {target_path}: {e}")
            # Clean up the temporary file if it exists
            if temp_file_path and await aiofiles.os.path.exists(temp_file_path):
                try:
                    await aiofiles.os.remove(temp_file_path)
                except Exception as cleanup_e:
                    logger.error(
                        f"Failed to clean up temporary file {temp_file_path}: {cleanup_e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to overwrite file: {str(e)}")
        finally:
            await file.close()
