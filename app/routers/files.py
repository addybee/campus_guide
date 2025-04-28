#!/usr/bin/env python3
"""
This module defines a FastAPI router for handling file-related operations,
including uploading, retrieving, updating, and deleting files. It supports
both GeoJSON/KML files and image files, with validation and database
integration.
"""

import os
from typing import List, Union
from fastapi import (
    APIRouter, Form, UploadFile, status, HTTPException, Depends
)
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.database import get_session
from app.models import GeoFile, ImageFile
from app.schema import UploadedFileInfo, UploadFilesResponse
from app.utility.file_services import GEO_MIME_TYPES
from app.utility.db_services import CRUDService
from app import ALLOWED_MIME_TYPES

router = APIRouter()


@router.get('/files/{file_type}/{file_name}', status_code=status.HTTP_200_OK, response_model=None, tags=["Files"])
async def get_file(
    file_name: str,
    file_type: str,
    db: Session = Depends(get_session)
) -> Union[JSONResponse, FileResponse]:
    """
    Retrieves a file (GeoJSON or Image) for a given institution based on file
    type.

    Args:
        file_name: The name of the file to retrieve.
        file_type: Query parameter specifying the type ("geo" for GeoJSON,
                   "image" for image).
        db: Database session dependency.

    Returns:
        JSONResponse if file_type is "geo" (with the file content loaded as
        JSON), or FileResponse if file_type is "image".
    """
    service: CRUDService = CRUDService(db)

    if file_type == "geo":
        geo_file: GeoFile = await service.get_geo_file(file_name)
        content = await service.get_geojson_file_content(geo_file.path)
        return JSONResponse(content=content, status_code=status.HTTP_200_OK)
    elif file_type == "image":
        image_file: ImageFile = await service.get_image_file(file_name)
        if not os.path.exists(image_file.path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image file not found on disk"
            )
        return FileResponse(image_file.path, media_type=image_file.content_type)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type."
        )


@router.post('/files/', status_code=status.HTTP_201_CREATED, tags=["Files"])
async def upload_file(
    files: List[UploadFile],
    institution_id: str = Form(...),
    db: Session = Depends(get_session)
) -> UploadFilesResponse:
    """
    Handles multiple file uploads.

    Validates each file's MIME type, checks for duplicates for the institution,
    and then saves the file (using synchronous I/O in a threadpool). For KML
    files, the file is converted to GeoJSON. Creates corresponding database
    entries (GeoFile or ImageFile) and returns the inserted records.

    Args:
        files: List of files uploaded via multipart/form-data.
        institution_id: The institution's ID as a form field.
        db: Database session dependency.

    Returns:
        A FileUploaded object containing lists of created geo and image files.
    """
    service: CRUDService = CRUDService(db)
    geo_files: List[GeoFile] = []
    image_files: List[ImageFile] = []

    for file in files:
        # Validate the MIME type.
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type '{file.content_type}'. "
                       f"Allowed types are images, GeoJSON, or KML."
            )

        is_geo: bool = file.content_type in GEO_MIME_TYPES

        # Check if a file with the same name already exists for the institution.
        if service.file_exists(institution_id, is_geo):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File with name '{file.filename}' already exists "
                       f"for institution."
            )

        # Save the file using a synchronous function in a threadpool.
        saved_file = await service.create_file(file, institution_id)

        if is_geo:
            geo_files.append(saved_file)
        else:
            image_files.append(saved_file)

    # Convert SQLAlchemy models to Pydantic schemas.
    return UploadFilesResponse(
        msg="Files uploaded successfully",
        geo_files=[UploadedFileInfo.model_validate(geo) for geo in geo_files],
        image_files=[UploadedFileInfo.model_validate(image) for image in image_files]
    )


@router.put('/files/{file_type}/{file_name}', status_code=status.HTTP_200_OK, tags=["Files"])
async def update_file(
    file: UploadFile,
    file_name: str,
    file_type: str,
    db: Session = Depends(get_session)
) -> UploadedFileInfo:
    """
    Updates an existing file for a given institution.

    Replaces the existing file (identified by file_name) with the new file
    provided.

    Args:
        file: The new file uploaded via multipart/form-data.
        file_name: The unique name of the file to update.
        db: Database session dependency.

    Returns:
        The updated file record as a FileGet.
    """
    if file_type not in ["geo", "image"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Must be 'geo' or 'image'."
        )
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{file.content_type}'. "
                   f"Allowed types are images, GeoJSON, or KML."
        )
    service: CRUDService = CRUDService(db)
    is_geo: bool = file_type == "geo"
    updated_file = await service.update_file(file, file_name, is_geo)
    return UploadedFileInfo.model_validate(updated_file)


@router.delete('/files/{file_type}/{file_name}', status_code=status.HTTP_200_OK, tags=["Files"])
async def delete_file(
    file_name: str,
    file_type: str,
    db: Session = Depends(get_session)
) -> dict:
    """
    Deletes a file (GeoJSON or Image) for a given institution.

    Args:
        file_name: The unique name of the file to delete.
        file_type: Query parameter specifying the type ("geo" or "image").
        db: Database session dependency.

    Returns:
        A dictionary with a success message.
    """
    service: CRUDService = CRUDService(db)

    if file_type == "geo":
        await service.delete_geo_file(file_name)
    elif file_type == "image":
        await service.delete_image_file(file_name)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Must be 'geo' or 'image'."
        )
    return {"msg": f"{file_name} deleted successfully"}
