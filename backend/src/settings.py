import os
import logging
from typing import Any, Dict

import pandas as pd
from pydantic_settings import BaseSettings
from pydantic import field_validator

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(asctime)s - %(funcName)s - %(message)s",
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
    BENTOML_URL: str = "http://localhost:3000/render"
    # API_KEY: Dict[str, Any] = {}
    FTP_URL: str = "http://49.156.55.124/raw"

    AUTHORIZED_PATH: str = "authorized.json"

    class Config:
        env_file = ".env"

    @field_validator("AUTHORIZED_PATH")
    def conv(cls, path: str = "authorized.json"):
        path = os.path.join(basedir, "authorized/" + path)
        logging.info(path)
        if not os.path.exists(path):
            return ""
        try:
            df = pd.read_json(path)
            df = df[["service_name", "api_key"]]
            df = df.dropna()
            df = df.drop_duplicates(subset=["api_key"])
            df = df.drop_duplicates(subset=["service_name"])
            df.to_json(path, orient="records", indent=4)
            cls.API_KEY = df.to_dict("list")
            return path
        except Exception:
            return ""


settings = Settings()
