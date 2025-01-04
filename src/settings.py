from pydantic import BaseModel
from typing import Any
import yaml
import os

class BotSetting(BaseModel):
    host: str
    password: str # Top secret KEK
    name: str # Friendly name
    label: str # PT config name
    template: str # Location in ./conf
    interval: int # 14400 or 86400 for now
    upload: bool = False
    defaults: dict[str, Any]

class Settings(BaseModel):
    predictions_api: str
    configs: list[BotSetting] = []

file = os.environ.get('CONF_FILE') or './conf/settings.yml'
with open(file, 'r') as stream: config = yaml.safe_load(stream)
settings = Settings(**config)
