#!/usr/bin/python3
"""
This module defines the SQLAlchemy models for the application, including
`Institution`, `GeoFile`, and `ImageFile`. These models represent the database
schema and include relationships between institutions and their associated
files.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Institution(Base):
    """
    Representation of an Institution.

    Attributes:
        id (str): Unique identifier for the institution.
        created_at (datetime): Timestamp when the institution was created.
        updated_at (datetime): Timestamp when the institution was last updated.
        name (str): Name of the institution (unique).
        country (str): Country where the institution is located.
        address (str): Address of the institution.
        chapter_name (str): Name of the chapter associated with the institution.
        OSM_mapping (int): Number of OpenStreetMap mappings contributed.
        contributor_full_name (str): Full name of the contributor.
        contributor_email (str): Email of the contributor (unique).
        contributor_phone_number (str): Phone number of the contributor.
        role_in_chapter (str): Role of the contributor in the chapter.
        geo_file (GeoFile): Relationship to the GeoFile associated with the institution.
        image_file (ImageFile): Relationship to the ImageFile associated with the institution.
    """

    __tablename__ = 'institutions'
    id = Column(
        String(60), primary_key=True, default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    name = Column(String(128), nullable=False, unique=True)
    country = Column(String(128), nullable=False)
    address = Column(String(128), nullable=False)
    chapter_name = Column(String(128), nullable=False)
    OSM_mapping = Column(Integer, nullable=False, default=0)
    contributor_full_name = Column(String(128), nullable=False)
    contributor_email = Column(String(128), nullable=False, unique=True)
    contributor_phone_number = Column(String(30), nullable=False)
    role_in_chapter = Column(String(128), nullable=True)
    geo_file = relationship(
        'GeoFile', backref='institution', uselist=False, lazy=True,
        cascade="all, delete-orphan"
    )
    image_file = relationship(
        'ImageFile', backref='institution', uselist=False, lazy=True,
        cascade="all, delete-orphan"
    )


class GeoFile(Base):
    """
    Representation of a GeoFile.

    Attributes:
        id (str): Unique identifier for the GeoFile.
        created_at (datetime): Timestamp when the GeoFile was created.
        updated_at (datetime): Timestamp when the GeoFile was last updated.
        name (str): Name of the GeoFile (unique).
        content_type (str): MIME type of the GeoFile.
        size (int): Size of the GeoFile in bytes.
        url (str): URL to access the GeoFile.
        path (str): File system path to the GeoFile.
        institution_id (str): Foreign key linking the GeoFile to an institution.
    """

    __tablename__ = 'geofiles'
    id = Column(
        String(60), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    name = Column(String(60), nullable=False, unique=True)
    content_type = Column(String(60), nullable=False)
    size = Column(Integer, nullable=False)
    url = Column(String(128), nullable=False)
    path = Column(String(128), nullable=False)
    institution_id = Column(
        String(128), ForeignKey('institutions.id'), nullable=False
    )


class ImageFile(Base):
    """
    Representation of an ImageFile.

    Attributes:
        id (str): Unique identifier for the ImageFile.
        created_at (datetime): Timestamp when the ImageFile was created.
        updated_at (datetime): Timestamp when the ImageFile was last updated.
        name (str): Name of the ImageFile (unique).
        content_type (str): MIME type of the ImageFile.
        size (int): Size of the ImageFile in bytes.
        url (str): URL to access the ImageFile.
        path (str): File system path to the ImageFile.
        institution_id (str): Foreign key linking the ImageFile to an institution.
    """

    __tablename__ = 'imagefiles'
    id = Column(
        String(60), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    name = Column(String(60), nullable=False, unique=True)
    content_type = Column(String(60), nullable=False)
    size = Column(Integer, nullable=False)
    url = Column(String(128), nullable=False)
    path = Column(String(128), nullable=False)
    institution_id = Column(
        String(128), ForeignKey('institutions.id'), nullable=False
    )