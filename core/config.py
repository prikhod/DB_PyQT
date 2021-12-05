import os
from typing import Any, Dict, Optional, Union
from pydantic import BaseSettings, validator, PostgresDsn


class Settings(BaseSettings):
    PROJECT_NAME: str
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: Union[PostgresDsn, str] = None
    if os.environ.get("MODE") != 'PROD':
        SQLALCHEMY_DATABASE_URI = 'sqlite:///./messenger.sqlite3'
    else:
        @validator("SQLALCHEMY_DATABASE_URI", pre=True)
        def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
            if isinstance(v, str):
                return v

            return PostgresDsn.build(
                scheme="postgresql",
                user=values.get("POSTGRES_USER"),
                password=values.get("POSTGRES_PASSWORD"),
                host=values.get("POSTGRES_SERVER"),
                path=f"/{values.get('POSTGRES_DB') or ''}",
            )


settings = Settings(_env_file='.env', _env_file_encoding='utf-8')
