"""Validation lookup endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.schemas.validation import ValidationResponse
from app.services import validation as validation_service

router = APIRouter()


@router.get("/validations/{validation_id}", response_model=ValidationResponse)
async def get_validation(validation_id: str) -> ValidationResponse:
    record = validation_service.get_validation(validation_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Validation not found")
    return validation_service.to_validation_response(record)
