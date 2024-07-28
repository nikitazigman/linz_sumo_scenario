from functools import lru_cache
from pathlib import Path

from h2mob.settings import general, volume_profile


class ScenarioConfig(general.GeneralConfig):
    template_path: Path = general.ROOT_UTILS_PATH / "template"

    vehicle_type_name: str = "vehicle"
    volume_profile: dict[int, float] = volume_profile.traffic_volume_profile

    min_trip_distance_m: int = 1500
    max_trip_distance_m: int = 30000
    prefix: str = "vehicle"


@lru_cache(maxsize=1)
def get_scenario_conf() -> ScenarioConfig:
    return ScenarioConfig()
