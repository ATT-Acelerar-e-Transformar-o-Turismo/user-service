from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional

from .config import settings
from .exceptions import DatabaseConnectionError


class DatabaseManager:
    """Manages MongoDB connection lifecycle using pydantic-settings configuration."""

    def __init__(self) -> None:
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None

    @property
    def client(self) -> AsyncIOMotorClient:
        if self._client is None:
            raise DatabaseConnectionError("Database client not initialized. Call connect() first.")
        return self._client

    @property
    def database(self) -> AsyncIOMotorDatabase:
        if self._database is None:
            raise DatabaseConnectionError("Database not initialized. Call connect() first.")
        return self._database

    async def connect(self) -> None:
        """Establish database connection using configuration from pydantic-settings."""
        if self._client is None:
            self._client = AsyncIOMotorClient(settings.MONGODB_URL)
            self._database = self._client[settings.DATABASE_NAME]

    async def disconnect(self) -> None:
        """Close database connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None

    def get_collection(self, collection_name: str):
        """Get a specific collection from the database."""
        return self.database[collection_name]


db_manager = DatabaseManager()


async def get_database() -> AsyncIOMotorDatabase:
    """Dependency injection for database access."""
    return db_manager.database


def get_collection(collection_name: str):
    """Get a specific collection by name."""
    return db_manager.get_collection(collection_name)