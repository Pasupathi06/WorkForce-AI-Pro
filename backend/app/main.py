from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.ai_monitoring import router as ai_monitoring_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.attendance import router as attendance_router
from app.api.routes.attrition import router as attrition_router
from app.api.routes.audit_logs import router as audit_logs_router
from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.departments import router as departments_router
from app.api.routes.documents import router as documents_router
from app.api.routes.employees import router as employees_router
from app.api.routes.leaves import router as leaves_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.payroll import router as payroll_router
from app.api.routes.performance import router as performance_router
from app.api.routes.reports import router as reports_router
from app.api.routes.tasks import router as tasks_router
from app.core.config import settings
from app.db.database import Base, engine
import app.models  # Ensures all models are registered with Base metadata


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Initialize database tables when the application starts."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "WorkForce AI Pro is an HR workforce intelligence platform "
        "for employee management, attrition prediction, and analytics."
    ),
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["System"], summary="API welcome endpoint")
def root() -> dict[str, str]:
    """Return basic application information."""
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "documentation": "/docs",
    }


@app.get("/health", tags=["System"], summary="Application health check")
def health_check() -> dict[str, str]:
    """Return the application health status."""
    return {
        "status": "healthy",
        "application": settings.APP_NAME,
    }


app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

app.include_router(
    departments_router,
    prefix="/api/v1/departments",
    tags=["Departments"],
)

app.include_router(
    employees_router,
    prefix="/api/v1/employees",
    tags=["Employees"],
)

app.include_router(attrition_router)

app.include_router(
    analytics_router,
    prefix="/api/v1/analytics",
    tags=["Workforce Analytics"],
)

app.include_router(
    attendance_router,
    prefix="/api/v1/attendance",
    tags=["Attendance & Shifts"],
)

app.include_router(
    leaves_router,
    prefix="/api/v1/leaves",
    tags=["Leave Management"],
)

app.include_router(
    payroll_router,
    prefix="/api/v1/payroll",
    tags=["Payroll Management"],
)

app.include_router(
    notifications_router,
    prefix="/api/v1/notifications",
    tags=["Notifications & Alerts"],
)

app.include_router(
    chat_router,
    prefix="/api/v1/chat",
    tags=["Chat & Communication"],
)

app.include_router(
    documents_router,
    prefix="/api/v1/documents",
    tags=["Document Management"],
)

app.include_router(
    tasks_router,
    prefix="/api/v1/tasks",
    tags=["Tasks & Workflow"],
)

app.include_router(
    performance_router,
    prefix="/api/v1/performance",
    tags=["Performance Reviews"],
)

app.include_router(
    audit_logs_router,
    prefix="/api/v1/audit-logs",
    tags=["Audit Logs"],
)

app.include_router(
    reports_router,
    prefix="/api/v1/reports",
    tags=["Reports & Exports"],
)

app.include_router(
    ai_monitoring_router,
    prefix="/api/v1/ai-monitoring",
    tags=["AI Workforce Monitoring"],
)
