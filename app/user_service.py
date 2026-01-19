from typing import Optional, List
from bson import ObjectId
from bson.errors import InvalidId
import logging

from .config import settings
from .database import get_collection
from .models import User, UserCreate, UserResponse
from .auth import get_password_hash, verify_password
from .exceptions import (
    UserAlreadyExistsError,
    LastAdminProtectionError,
    InvalidRoleError
)

logger = logging.getLogger(__name__)


COLLECTION_NAME = "users"
VALID_ROLES = {"admin", "user"}


class UserService:
    def __init__(self) -> None:
        self._collection_name = COLLECTION_NAME

    @property
    def collection(self):
        return get_collection(self._collection_name)

    def _to_user_response(self, user: User) -> UserResponse:
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at
        )

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise UserAlreadyExistsError(f"Email already registered: {user_data.email}")

        hashed_password = get_password_hash(user_data.password)
        user_dict = user_data.model_dump(exclude={"password"})
        user_dict["hashed_password"] = hashed_password

        result = await self.collection.insert_one(user_dict)
        user_dict["_id"] = str(result.inserted_id)

        user = User(**user_dict)
        return self._to_user_response(user)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        user_data = await self.collection.find_one({"email": email})
        if user_data:
            user_data["_id"] = str(user_data["_id"])
            return User(**user_data)
        return None

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        try:
            user_data = await self.collection.find_one({"_id": ObjectId(user_id)})
            if user_data:
                user_data["_id"] = str(user_data["_id"])
                return User(**user_data)
        except InvalidId as e:
            logger.warning(f"Invalid ObjectId format for user_id={user_id}: {e}")
            return None
        return None

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def update_user(self, user_id: str, update_data: dict) -> Optional[UserResponse]:
        try:
            await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            updated_user = await self.get_user_by_id(user_id)
            if updated_user:
                return self._to_user_response(updated_user)
        except InvalidId as e:
            logger.error(f"Invalid ObjectId format for user_id={user_id}: {e}")
            return None
        return None

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        cursor = self.collection.find().skip(skip).limit(limit)
        users = []
        async for user_data in cursor:
            user_data["_id"] = str(user_data["_id"])
            user = User(**user_data)
            users.append(self._to_user_response(user))
        return users

    async def count_admin_users(self) -> int:
        count = await self.collection.count_documents({"role": "admin"})
        return count

    async def update_user_role(self, user_id: str, role: str) -> Optional[UserResponse]:
        if role not in VALID_ROLES:
            raise InvalidRoleError(f"Invalid role: {role}")

        if role == "user":
            current_user = await self.get_user_by_id(user_id)
            if current_user and current_user.role == "admin":
                admin_count = await self.count_admin_users()
                if admin_count <= 1:
                    raise LastAdminProtectionError("Cannot remove admin role from the last administrator")

        return await self.update_user(user_id, {"role": role})

    async def delete_user(self, user_id: str) -> bool:
        user_to_delete = await self.get_user_by_id(user_id)
        if user_to_delete and user_to_delete.role == "admin":
            admin_count = await self.count_admin_users()
            if admin_count <= 1:
                raise LastAdminProtectionError("Cannot delete the last administrator")

        result = await self.collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0

    async def create_default_admin(self) -> Optional[UserResponse]:
        admin_email = settings.DEFAULT_ADMIN_EMAIL
        admin_password = settings.DEFAULT_ADMIN_PASSWORD
        admin_name = settings.DEFAULT_ADMIN_NAME

        existing_admin = await self.get_user_by_email(admin_email)
        if existing_admin:
            return None

        try:
            admin_data = UserCreate(
                email=admin_email,
                password=admin_password,
                full_name=admin_name,
                role="admin"
            )

            admin_user = await self.create_user(admin_data)
            return admin_user

        except (ValueError, UserAlreadyExistsError) as e:
            logger.error(f"Failed to create default admin: {e}")
            return None


def get_user_service() -> UserService:
    return UserService()
