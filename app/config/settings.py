from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    DB_PORT: int = 5432
    DB_HOST: str = 'localhost'

    TEST_DB_USER: str
    TEST_DB_PASS: str
    TEST_DB_NAME: str
    TEST_DB_PORT: int = 5432
    TEST_DB_HOST: str = 'localhost'

    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = 'HS256'

    POSTGRES_HOST: str = 'localhost'

    DATABASE_URL: Optional[str] = None
    TEST_DATABASE_URL: Optional[str] = None

    def model_post_init(self, context: Any) -> None:
        if not self.DATABASE_URL:
            self.DATABASE_URL = f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'
        if not self.TEST_DATABASE_URL:
            self.TEST_DATABASE_URL = f'postgresql+asyncpg://{self.TEST_DB_USER}:{self.TEST_DB_PASS}@{self.TEST_DB_HOST}:{self.TEST_DB_PORT}/{self.TEST_DB_NAME}'

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / '.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )


settings = Settings()
