from pydantic import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    app_name: str = "Awesome API"
    admin_email: str = '1@1.ru'
    items_per_user: int = 50
    wms_token: str = os.getenv("wms_token", "lol")
    wms_url: str = os.getenv("wms_url", "lol")
    DB_PASSWORD: str = 'test'
    DB_NAME: str = 'stub'
    DB_USER: str = 'taxi'
    DB_HOST: str = 'localhost'

    class Config:
        env_file = ".env"

settings = Settings()

@lru_cache()
def get_settings():
    return Settings()
