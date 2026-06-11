from pydantic import BaseModel
from typing import Optional


class ApplicationData(BaseModel):
    brand_name: str
    class_type: Optional[str] = None
    alcohol_content: Optional[str] = None
    net_contents: Optional[str] = None
    producer_name: Optional[str] = None
    producer_address: Optional[str] = None
    country_of_origin: Optional[str] = None


class FieldResult(BaseModel):
    field: str
    expected: Optional[str]
    extracted: Optional[str]
    passed: bool
    note: Optional[str] = None


class VerificationResult(BaseModel):
    filename: str
    overall_passed: bool
    fields: list[FieldResult]
    government_warning_present: bool
    government_warning_exact: bool
    raw_extracted_text: Optional[str] = None
    error: Optional[str] = None


class BatchVerificationResponse(BaseModel):
    results: list[VerificationResult]
    total: int
    passed: int
    failed: int
