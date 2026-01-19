from fastapi import HTTPException, status


class UserServiceException(Exception):
    """Base exception for user-service."""
    pass


class DatabaseConnectionError(UserServiceException):
    """Raised when database connection fails or is not initialized."""
    pass


class UserNotFoundError(UserServiceException):
    """Raised when a user is not found."""
    pass


class UserAlreadyExistsError(UserServiceException):
    """Raised when attempting to create a duplicate user."""
    pass


class InvalidCredentialsError(UserServiceException):
    """Raised when authentication credentials are invalid."""
    pass


class LastAdminProtectionError(UserServiceException):
    """Raised when attempting to delete or demote the last admin."""
    pass


class InvalidRoleError(UserServiceException):
    """Raised when an invalid role is specified."""
    pass


def user_not_found(user_id: str) -> HTTPException:
    """Create HTTPException for user not found."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"User with id {user_id} not found"
    )


def user_already_exists(email: str) -> HTTPException:
    """Create HTTPException for duplicate user."""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"User with email {email} already exists"
    )


def invalid_credentials() -> HTTPException:
    """Create HTTPException for invalid credentials."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
        headers={"WWW-Authenticate": "Bearer"}
    )


def last_admin_protection() -> HTTPException:
    """Create HTTPException for last admin protection."""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Cannot delete or demote the last administrator"
    )


def invalid_role(role: str) -> HTTPException:
    """Create HTTPException for invalid role."""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Invalid role: {role}. Must be 'admin' or 'user'"
    )
