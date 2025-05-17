#!/usr/bin/env python3
"""
This module defines a FastAPI router for handling institution-related
operations, including retrieving, creating, updating, and deleting
institutions.
"""

from typing import List
from sqlalchemy.orm import Session
from app.database import get_session
from app.models import Institution
from app.schema import InstitutionGet, InstitutionPost, InstitutionUpdate

from fastapi import APIRouter, status, HTTPException, Depends

from app.utility.db_services import CRUDService

router = APIRouter()


@router.get(
    '/institutions',
    status_code=status.HTTP_200_OK,
    response_model=List[InstitutionGet],
    tags=["Institution"]
)
async def get_institutions(db: Session = Depends(get_session)) -> List[InstitutionGet]:
    """
    Retrieves all institutions from the database.

    Args:
        db: Database session dependency.

    Returns:
        A list of institutions as InstitutionGet.
    """
    service: CRUDService = CRUDService(db)
    return service.get_institutions()


@router.get(
    '/institution/{institution_id}',
    status_code=status.HTTP_200_OK,
    tags=["Institution"]
)
async def get_institution_by_id(
    institution_id: str,
    db: Session = Depends(get_session)
) -> InstitutionGet:
    """
    Retrieves an institution by its ID.

    Args:
        institution_id: The institution's ID.
        db: Database session dependency.

    Returns:
        The institution as InstitutionGet.
    """
    service: CRUDService = CRUDService(db)
    return service.get_institution_by_id(institution_id)


@router.post(
    '/institution',
    status_code=status.HTTP_201_CREATED,
    tags=["Institution"]
)
async def create_institution(
    institution: InstitutionPost,
    db: Session = Depends(get_session)
) -> InstitutionGet:
    """
    Creates a new institution.

    Args:
        institution: Institution data in the request body.
        db: Database session dependency.

    Returns:
        The created Institution as InstitutionGet.
    """
    service: CRUDService = CRUDService(db)
    if service.institution_exists(institution.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Institution already exists"
        )
    new_institution: Institution = Institution(**institution.model_dump())
    return service.create_institution(new_institution)


@router.put(
    '/institution/{institution_id}',
    status_code=status.HTTP_200_OK,
    tags=["Institution"]
)
async def update_institution(
    institution_id: str,
    institution: InstitutionUpdate,
    db: Session = Depends(get_session)
) -> InstitutionGet:
    """
    Updates an existing institution.

    Args:
        institution_id: The institution's ID.
        institution: Updated institution data in the request body.
        db: Database session dependency.

    Returns:
        The updated Institution as InstitutionGet.
    """
    service: CRUDService = CRUDService(db)
    return service.update_institution(institution_id, institution.model_dump())


@router.delete(
    '/institution/{institution_id}',
    status_code=status.HTTP_200_OK,
    response_model=None,
    tags=["Institution"]
)
async def delete_institution(
    institution_id: str,
    db: Session = Depends(get_session)
) -> dict:
    """
    Deletes an institution by its ID.

    Args:
        institution_id: The institution's ID.
        db: Database session dependency.

    Returns:
        A message indicating successful deletion.
    """
    service: CRUDService = CRUDService(db)
    await service.delete_institution(institution_id)
    return {"msg": "Institution deleted successfully"}
