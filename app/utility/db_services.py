#!/usr/bin/env python3
"""
This module provides a `CRUDService` class for handling database operations
related to institutions and files. It includes methods for creating, retrieving,
updating, and deleting institutions and files, with proper validation and
integration with the filesystem.
"""

from datetime import datetime
import os
from pathlib import Path
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.models import Institution, GeoFile, ImageFile
from app.utility.file_services import FileHandler
from app import GEO_MIME_TYPES


class CRUDService:
    """
    A service class for handling CRUD operations on institutions and files.

    Attributes:
        db (Session): The database session used for querying and committing.
    """

    def __init__(self, db: Session):
        """
        Initializes the CRUDService with a database session.

        Args:
            db (Session): The database session.
        """
        self.db = db

    # ----------------- INSTITUTION ----------------- #

    def institution_exists(self, name: str) -> bool:
        """
        Checks if an institution with the given name exists.

        Args:
            name (str): The name of the institution.

        Returns:
            bool: True if the institution exists, False otherwise.
        """
        return self.db.query(Institution).filter(
            Institution.name == name
        ).first() is not None

    def create_institution(self, institution: Institution) -> Institution:
        """
        Creates a new institution in the database.

        Args:
            institution (Institution): The institution to create.

        Returns:
            Institution: The created institution.
        """
        self.db.add(institution)
        self.db.commit()
        self.db.refresh(institution)
        return institution

    def get_institution_by_id(self, institution_id: str) -> Institution:
        """
        Retrieves an institution by its ID.

        Args:
            institution_id (str): The ID of the institution.

        Returns:
            Institution: The retrieved institution.

        Raises:
            HTTPException: If the institution is not found.
        """
        institution = self.db.query(Institution).filter(
            Institution.id == institution_id
        ).first()
        if not institution:
            raise HTTPException(status_code=404, detail="Institution not found")
        return institution

    def update_institution(self, institution_id: str, updates: dict) -> Institution:
        """
        Updates an existing institution with the given updates.

        Args:
            institution_id (str): The ID of the institution to update.
            updates (dict): A dictionary of fields to update.

        Returns:
            Institution: The updated institution.
        """
        institution = self.get_institution_by_id(institution_id)
        for field, value in updates.items():
            if value is not None:
                setattr(institution, field, value)
        self.db.commit()
        self.db.refresh(institution)
        return institution

    async def delete_institution(self, institution_id: str):
        """
        Deletes an institution by its ID.

        Args:
            institution_id (str): The ID of the institution to delete.
        """
        institution = self.get_institution_by_id(institution_id)
        await FileHandler.delete_file(Path(institution.geo_file.path))
        await FileHandler.delete_file(Path(institution.image_file.path))
        self.db.delete(institution)
        self.db.commit()

    # ----------------- FILES ----------------- #

    def file_exists(self, institution_id: str, is_geo: bool) -> bool:
        """
        Checks if a file exists for a given institution.

        Args:
            institution_id (str): The ID of the institution.
            is_geo (bool): Whether the file is a GeoJSON file.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        model = GeoFile if is_geo else ImageFile
        return self.db.query(model).filter(
            model.institution_id == institution_id
        ).first() is not None

    async def create_file(self, file: UploadFile, institution_id: str):
        """
        Creates a new file (GeoJSON or image) for a given institution.

        Args:
            file (UploadFile): The uploaded file.
            institution_id (str): The ID of the institution.

        Returns:
            GeoFile or ImageFile: The created file record.
        """
        file_path = await FileHandler.save_file(file)

        file_model = GeoFile if file.content_type in GEO_MIME_TYPES else ImageFile
        file_label = "geo" if file_model == GeoFile else "image"
        base_url = f"localhost:8000/api/v1/files/{file_label}/"
        new_file = file_model(
            name=str(file_path.name),
            content_type=file.content_type,
            path=str(file_path),
            institution_id=institution_id,
            size=os.path.getsize(file_path),
            url=base_url + str(file_path.name)
        )

        self.db.add(new_file)
        self.db.commit()
        self.db.refresh(new_file)
        return new_file

    async def get_geo_file(self, file_name: str) -> GeoFile:
        """
        Retrieves a GeoJSON file by its name.

        Args:
            file_name (str): The name of the file.

        Returns:
            GeoFile: The retrieved GeoJSON file.
        """
        return await self._get_file_or_404(GeoFile, file_name, "GeoFile")

    async def get_geojson_file_content(self, path: str) -> dict:
        """
        Loads the content of a GeoJSON file.

        Args:
            path (str): The path to the GeoJSON file.

        Returns:
            dict: The content of the GeoJSON file.
        """
        return await FileHandler.load_geojson_content(Path(path))

    async def get_image_file(self, file_name: str) -> ImageFile:
        """
        Retrieves an image file by its name.

        Args:
            file_name (str): The name of the file.

        Returns:
            ImageFile: The retrieved image file.
        """
        return await self._get_file_or_404(ImageFile, file_name, "ImageFile")

    async def delete_geo_file(self, file_name: str):
        """
        Deletes a GeoJSON file by its name.

        Args:
            file_name (str): The name of the GeoJSON file.
        """
        geo_file = await self.get_geo_file(file_name)
        await self._delete_file(geo_file)

    async def delete_image_file(self, file_name: str):
        """
        Deletes an image file by its name.

        Args:
            file_name (str): The name of the image file.
        """
        image_file = await self.get_image_file(file_name)
        await self._delete_file(image_file)

    async def update_file(self, file: UploadFile, file_name: str, is_geo: bool):
        """
        Updates an existing file by overwriting it with a new file.

        Args:
            file (UploadFile): The new file to upload.
            file_name (str): The name of the existing file.
            is_geo (bool): Whether the file is a GeoJSON file.

        Returns:
            GeoFile or ImageFile: The updated file record.
        """
        file_model, file_label = [GeoFile, 'Geo File'] if is_geo else [ImageFile, 'Image File']
        existing_file = await self._get_file_or_404(file_model, file_name, file_label)

        await FileHandler.overwrite_file(file, Path(existing_file.path))
        existing_file.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(existing_file)
        return existing_file

    # ----------------- PRIVATE HELPERS ----------------- #

    async def _get_file_or_404(self, model, file_name: str, file_label: str):
        """
        Retrieves a file by its name or raises a 404 error if not found.

        Args:
            model: The SQLAlchemy model (GeoFile or ImageFile).
            file_name (str): The name of the file.
            file_label (str): A label for the file type (e.g., "GeoFile").

        Returns:
            GeoFile or ImageFile: The retrieved file.

        Raises:
            HTTPException: If the file is not found in the database or filesystem.
        """
        file = self.db.query(model).filter(model.name == file_name).first()
        if not file or not await FileHandler.file_exists(Path(file.path)):
            if file:
                raise HTTPException(
                    status_code=404,
                    detail=f"{file_label} found in DB but missing in filesystem"
                )
            raise HTTPException(status_code=404, detail=f"{file_label} not found")
        return file

    async def _delete_file(self, file):
        """
        Deletes a file from the filesystem and database.

        Args:
            file: The file record to delete.
        """
        await FileHandler.delete_file(Path(file.path))
        self.db.delete(file)
        self.db.commit()
