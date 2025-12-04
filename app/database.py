import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database = None

db = Database()

async def get_database() -> AsyncIOMotorClient:
    return db.database

async def connect_to_mongo():
    """Create database connection"""
    db.client = AsyncIOMotorClient(os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
    db.database = db.client.users

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()

def get_collection(collection_name: str):
    """Get a specific collection"""
    if db.database is None:
        raise RuntimeError("Database not connected. Make sure to call connect_to_mongo() first.")
    return db.database[collection_name]