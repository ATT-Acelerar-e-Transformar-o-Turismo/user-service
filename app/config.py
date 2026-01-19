from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ORIGINS: str = Field(default="localhost", env="ORIGINS")
    MONGODB_URL: str = Field(
        default="mongodb://localhost:27017", env="MONGODB_URL"
    )
    DATABASE_NAME: str = Field(default="users", env="DATABASE_NAME")

    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    DEFAULT_ADMIN_EMAIL: str = Field(
        default="admin@example.com", env="DEFAULT_ADMIN_EMAIL"
    )
    DEFAULT_ADMIN_PASSWORD: str = Field(
        default="admin", env="DEFAULT_ADMIN_PASSWORD"
    )
    DEFAULT_ADMIN_NAME: str = Field(
        default="Administrator", env="DEFAULT_ADMIN_NAME"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
