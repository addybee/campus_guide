#!/usr/bin/python3
"""
This module defines Pydantic models (schemas) for request and response
validation in the FastAPI application. These schemas ensure data consistency
and provide examples for API documentation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class UploadedFileInfo(BaseModel):
    """
    Schema for representing information about an uploaded file.

    Attributes:
        name (str): The name of the file (e.g., "file.geojson").
        content_type (str): The MIME type of the file (e.g., "application/geo+json").
        size (int): The size of the file in bytes.
        url (str): The URL where the file can be accessed.
    """
    name: str = Field(
        ...,
        json_schema_extra={"example": "file.geojson"}
    )
    content_type: str = Field(
        ...,
        json_schema_extra={"example": "application/geo+json"}
    )
    size: int = Field(
        ...,
        json_schema_extra={"example": 123456}
    )
    url: str = Field(
        ...,
        json_schema_extra={"example": "https://example.com/file.geojson"}
    )
    
    model_config= {"from_attributes": True}


class InstitutionPost(BaseModel):
    """
    Schema for creating a new institution.

    Attributes:
        name (str): The name of the institution.
        country (str): The country where the institution is located.
        address (str): The address of the institution.
        chapter_name (str): The name of the chapter associated with the institution.
        OSM_mapping (int): The number of OpenStreetMap mappings contributed.
        contributor_full_name (str): The full name of the contributor.
        contributor_email (str): The email of the contributor.
        contributor_phone_number (str): The phone number of the contributor.
        role_in_chapter (str): The role of the contributor in the chapter.
    """
    name: str
    country: str
    address: str
    chapter_name: str
    OSM_mapping: int
    contributor_full_name: str
    contributor_email: str
    contributor_phone_number: str
    role_in_chapter: str


class InstitutionGet(BaseModel):
    """
    Schema for retrieving institution details.

    Attributes:
        id (Optional[str]): The unique identifier of the institution.
        created_at (Optional[datetime]): The timestamp when the institution was created.
        updated_at (Optional[datetime]): The timestamp when the institution was last updated.
        name (str): The name of the institution.
        country (str): The country where the institution is located.
        address (str): The address of the institution.
        chapter_name (str): The name of the chapter associated with the institution.
        OSM_mapping (int): The number of OpenStreetMap mappings contributed.
        contributor_full_name (str): The full name of the contributor.
        contributor_email (str): The email of the contributor.
        contributor_phone_number (str): The phone number of the contributor.
        role_in_chapter (str): The role of the contributor in the chapter.
        geo_file (Optional[UploadedFileInfo]): Information about the associated GeoJSON file.
        image_file (Optional[UploadedFileInfo]): Information about the associated image file.
    """
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    name: str
    country: str
    address: str
    chapter_name: str
    OSM_mapping: int
    contributor_full_name: str
    contributor_email: str
    contributor_phone_number: str
    role_in_chapter: str
    geo_file: Optional[UploadedFileInfo] = None
    image_file: Optional[UploadedFileInfo] = None


class InstitutionUpdate(BaseModel):
    """
    Schema for updating institution details.

    Attributes:
        name (Optional[str]): The name of the institution.
        country (Optional[str]): The country where the institution is located.
        address (Optional[str]): The address of the institution.
        chapter_name (Optional[str]): The name of the chapter associated with the institution.
        OSM_mapping (Optional[int]): The number of OpenStreetMap mappings contributed.
        contributor_full_name (Optional[str]): The full name of the contributor.
        contributor_email (Optional[str]): The email of the contributor.
        contributor_phone_number (Optional[str]): The phone number of the contributor.
        role_in_chapter (Optional[str]): The role of the contributor in the chapter.
    """
    name: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    chapter_name: Optional[str] = None
    OSM_mapping: Optional[int] = None
    contributor_full_name: Optional[str] = None
    contributor_email: Optional[str] = None
    contributor_phone_number: Optional[str] = None
    role_in_chapter: Optional[str] = None


class UploadFilesResponse(BaseModel):
    """
    Schema for the response after uploading files.

    Attributes:
        msg (str): A success message.
        geo_files (List[UploadedFileInfo]): A list of uploaded GeoJSON files.
        image_files (List[UploadedFileInfo]): A list of uploaded image files.
        errors (Optional[List[str]]): A list of errors encountered during the upload process.
    """
    msg: str = Field(
        ...,
        json_schema_extra={"example": "Files uploaded successfully"}
    )
    geo_files: List[UploadedFileInfo] = Field(default_factory=list)
    image_files: List[UploadedFileInfo] = Field(default_factory=list)
    errors: Optional[List[str]] = Field(default_factory=list)
