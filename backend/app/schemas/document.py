from datetime import datetime
from pydantic import BaseModel, ConfigDict


class EmployeeDocumentCreate(BaseModel):
    employee_id: int
    title: str
    document_type: str  # CONTRACT, ID_PROOF, RESUME, TAX_FORM, CERTIFICATE, OTHER
    file_name: str
    file_path: str
    file_size_kb: float = 0.0


class EmployeeDocumentResponse(BaseModel):
    id: int
    employee_id: int
    title: str
    document_type: str
    file_name: str
    file_path: str
    file_size_kb: float
    uploaded_by_id: int
    created_at: datetime
    employee_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
