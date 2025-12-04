from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from .database import connect_to_mongo, close_mongo_connection
from .routes import router
from .user_service import get_user_service

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()

    # Create default admin user
    user_service = get_user_service()
    await user_service.create_default_admin()

    yield
    # Shutdown
    await close_mongo_connection()

app = FastAPI(
    title="User Service API",
    description="Authentication and user management service",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
origins = os.getenv("ORIGINS", "localhost").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/auth", tags=["authentication"])

@app.get("/")
def read_root():
    return {"message": "User Service API - Authentication and User Management"}
