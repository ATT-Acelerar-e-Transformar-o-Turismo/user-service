from typing import Optional
import os
from bson import ObjectId
from .database import get_collection
from .models import User, UserCreate, UserResponse
from .auth import get_password_hash, verify_password

class UserService:
    def __init__(self):
        self.collection_name = "users"

    @property
    def collection(self):
        return get_collection(self.collection_name)

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user"""
        # Check if user already exists
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise ValueError("Email already registered")

        # Hash password and create user
        hashed_password = get_password_hash(user_data.password)
        user_dict = user_data.model_dump(exclude={"password"})
        user_dict["hashed_password"] = hashed_password

        result = await self.collection.insert_one(user_dict)
        user_dict["_id"] = str(result.inserted_id)

        user = User(**user_dict)
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at
        )

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        user_data = await self.collection.find_one({"email": email})
        if user_data:
            user_data["_id"] = str(user_data["_id"])
            return User(**user_data)
        return None

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            user_data = await self.collection.find_one({"_id": ObjectId(user_id)})
            if user_data:
                user_data["_id"] = str(user_data["_id"])
                return User(**user_data)
        except Exception:
            return None
        return None

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def update_user(self, user_id: str, update_data: dict) -> Optional[UserResponse]:
        """Update user information"""
        try:
            await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            updated_user = await self.get_user_by_id(user_id)
            if updated_user:
                return UserResponse(
                    id=updated_user.id,
                    email=updated_user.email,
                    full_name=updated_user.full_name,
                    role=updated_user.role,
                    is_active=updated_user.is_active,
                    created_at=updated_user.created_at
                )
        except Exception:
            return None
        return None

    async def create_default_admin(self):
        """Create default admin user if it doesn't exist"""
        admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
        admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin")
        admin_name = os.getenv("DEFAULT_ADMIN_NAME", "Administrator")

        # Check if admin user already exists
        existing_admin = await self.get_user_by_email(admin_email)
        if existing_admin:
            print(f"Default admin user already exists: {admin_email}")
            return existing_admin

        # Create admin user
        try:
            admin_data = UserCreate(
                email=admin_email,
                password=admin_password,
                full_name=admin_name,
                role="admin"
            )

            admin_user = await self.create_user(admin_data)
            print(f"Default admin user created: {admin_email}")
            return admin_user

        except Exception as e:
            print(f"Error creating default admin user: {e}")
            return None

def get_user_service():
    return UserService()
