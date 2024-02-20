import os
import logging

from pydantic_settings import BaseSettings

logging.basicConfig(
    level=logging.INFO, format="%(levelname)s: %(asctime)s - %(funcName)s - %(message)s"
)
log = logging.getLogger("vsk")

basedir = os.path.abspath(os.path.dirname(__file__))


class Settings(BaseSettings):
    DEBUG: bool = False
    SHOW: bool = False
    TESTING: bool = False
    CSRF_ENABLED: bool = True
    SECRET_KEY: str = "this-really-needs-to-be-changed"
    DATABASE_URL: str
    DATABASE_HOST: str
    RABBITMQ_URL: str
    LIMIT: int = 300

    class Config:
        env_file = ".env"


settings = Settings()
