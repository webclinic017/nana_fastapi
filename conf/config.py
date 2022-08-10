from pydantic import BaseSettings
from functools import lru_cache
import os
wms_token = os.getenv("wms_token", "wms_token")
wms_url = os.getenv("wms_url", "wms_url")
class Settings(BaseSettings):
    app_name: str = "Awesome API"
    admin_email: str = '1@1.ru'
    items_per_user: int = 50
    wms_token: str = wms_token
    wms_url: str = wms_url
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
