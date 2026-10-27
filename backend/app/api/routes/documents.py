from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, HRUser
from app.db.database import get_db
from app.models.document import EmployeeDocument
from app.models.employee import Employee
from app.schemas.document import EmployeeDocumentCreate, EmployeeDocumentResponse

router = APIRouter()
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[EmployeeDocumentResponse], summary="List employee documents")
def list_documents(
    db: DatabaseSession,
    current_user: CurrentUser,
    employee_id: int | None = None,
    document_type: str | None = None,
    limit: int = Query(default=100, le=300),
):
    query = db.query(EmployeeDocument)
    if employee_id:
        query = query.filter(EmployeeDocument.employee_id == employee_id)
    if document_type:
        query = query.filter(EmployeeDocument.document_type == document_type)

    docs = query.order_by(EmployeeDocument.created_at.desc()).limit(limit).all()

    result = []
    for d in docs:
        item = EmployeeDocumentResponse.model_validate(d)
        if d.employee and d.employee.user:
            item.employee_name = d.employee.user.full_name
        elif d.employee:
            item.employee_name = d.employee.employee_code
        result.append(item)
    return result


@router.post(
    "/",
    response_model=EmployeeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register/Upload employee document",
)
def upload_document(
    data: EmployeeDocumentCreate, db: DatabaseSession, current_user: HRUser
):
    employee = db.query(Employee).filter(Employee.id == data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    doc = EmployeeDocument(
        employee_id=employee.id,
        title=data.title,
        document_type=data.document_type.upper(),
        file_name=data.file_name,
        file_path=data.file_path,
        file_size_kb=data.file_size_kb,
        uploaded_by_id=current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    item = EmployeeDocumentResponse.model_validate(doc)
    item.employee_name = employee.user.full_name if employee.user else employee.employee_code
    return item


@router.delete("/{doc_id}", summary="Delete an employee document")
def delete_document(doc_id: int, db: DatabaseSession, current_user: HRUser):
    doc = db.query(EmployeeDocument).filter(EmployeeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    db.delete(doc)
    db.commit()
    return {"message": "Document deleted successfully."}
