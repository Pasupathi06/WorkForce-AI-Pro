from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, HRUser
from app.db.database import get_db
from app.models.employee import Employee
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter()
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[TaskResponse], summary="List tasks")
def list_tasks(
    db: DatabaseSession,
    current_user: CurrentUser,
    assigned_to_id: int | None = None,
    status_filter: str | None = None,
    limit: int = Query(default=100, le=300),
):
    query = db.query(Task)
    if assigned_to_id:
        query = query.filter(Task.assigned_to_id == assigned_to_id)
    if status_filter:
        query = query.filter(Task.status == status_filter)

    tasks = query.order_by(Task.due_date.asc().nullslast(), Task.id.desc()).limit(limit).all()

    result = []
    for t in tasks:
        item = TaskResponse.model_validate(t)
        if t.assigned_to and t.assigned_to.user:
            item.assigned_to_name = t.assigned_to.user.full_name
        elif t.assigned_to:
            item.assigned_to_name = t.assigned_to.employee_code
        if t.created_by:
            item.created_by_name = t.created_by.full_name
        result.append(item)
    return result


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
def create_task(data: TaskCreate, db: DatabaseSession, current_user: CurrentUser):
    employee = db.query(Employee).filter(Employee.id == data.assigned_to_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Assigned employee not found.")

    task = Task(
        title=data.title,
        description=data.description,
        assigned_to_id=employee.id,
        created_by_id=current_user.id,
        priority=data.priority.upper(),
        status="PENDING",
        due_date=data.due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    item = TaskResponse.model_validate(task)
    item.assigned_to_name = employee.user.full_name if employee.user else employee.employee_code
    item.created_by_name = current_user.full_name
    return item


@router.patch("/{task_id}", response_model=TaskResponse, summary="Update task details or status")
def update_task(
    task_id: int, data: TaskUpdate, db: DatabaseSession, current_user: CurrentUser
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    if data.title is not None:
        task.title = data.title
    if data.description is not None:
        task.description = data.description
    if data.priority is not None:
        task.priority = data.priority.upper()
    if data.status is not None:
        task.status = data.status.upper()
    if data.due_date is not None:
        task.due_date = data.due_date

    db.commit()
    db.refresh(task)

    item = TaskResponse.model_validate(task)
    if task.assigned_to and task.assigned_to.user:
        item.assigned_to_name = task.assigned_to.user.full_name
    if task.created_by:
        item.created_by_name = task.created_by.full_name
    return item


@router.delete("/{task_id}", summary="Delete a task")
def delete_task(task_id: int, db: DatabaseSession, current_user: HRUser):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully."}
