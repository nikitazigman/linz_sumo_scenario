from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent.parent.parent
SUMO_DIR = BASE_DIR / "test_scenario/osm.sumocfg"


class Settings(BaseSettings):
    sumo_scenario: Path = SUMO_DIR


@lru_cache(maxsize=1)
def get_settings():
    return Settings()
