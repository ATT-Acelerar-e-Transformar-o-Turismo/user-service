from typing import Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings
from .database import db_manager
from .routes import router
from .user_routes import router as user_router
from .user_service import get_user_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_manager.connect()

    user_service = get_user_service()
    await user_service.create_default_admin()

    yield
    await db_manager.disconnect()


app = FastAPI(
    title="User Service API",
    description="Authentication and user management service",
    version="1.0.0",
    lifespan=lifespan
)

origins = settings.ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/auth", tags=["authentication"])
app.include_router(user_router, prefix="/users", tags=["user management"])


@app.get("/")
def read_root() -> Dict[str, str]:
    return {"message": "User Service API - Authentication and User Management"}
