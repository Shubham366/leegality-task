import json
import os
from pathlib import Path

from pydantic import BaseModel


class Config(BaseModel):
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    ENV: str = "local"
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379


def get_config() -> Config:
    env = os.getenv("ENV", "local")
    config_data = {}
    env_file = Path("env.json")
    if env_file.exists():
        with env_file.open() as json_env_file:
            config_data = json.load(json_env_file)
    config_data.setdefault("ENV", env)
    for key in Config.model_fields:
        if os.getenv(key):
            config_data[key] = os.environ[key]
    return Config(**config_data)


config: Config = get_config()
