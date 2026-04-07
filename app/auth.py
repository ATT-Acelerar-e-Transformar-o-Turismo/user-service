import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
import httpx
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import settings
from .models import TokenData

JWKS_URL = "http://att-keycloak:7080/auth/realms/att/protocol/openid-connect/certs"
ALGORITHMS_KC = ["RS256"]
JWKS_TTL = 300
_jwks_cache = None
_jwks_fetched_at = 0
_kc_security = HTTPBearer()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate bcrypt hash for a password."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, str], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with configurable expiration."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """Verify JWT token signature and extract payload data."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    return token_data


async def _get_jwks():
    global _jwks_cache, _jwks_fetched_at
    now = time.monotonic()
    if not _jwks_cache or (now - _jwks_fetched_at) > JWKS_TTL:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(JWKS_URL)
            resp.raise_for_status()
            _jwks_cache = resp.json()
            _jwks_fetched_at = now
    return _jwks_cache


def _get_signing_key(jwks, token):
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    if not kid:
        raise JWTError("Token header missing 'kid'")
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    raise JWTError("No matching key found")


async def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(_kc_security),
):
    token = credentials.credentials
    try:
        jwks = await _get_jwks()
        key = _get_signing_key(jwks, token)
        payload = jwt.decode(
            token, key, algorithms=ALGORITHMS_KC, options={"verify_aud": False}
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    roles = payload.get("realm_access", {}).get("roles", [])
    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return payload