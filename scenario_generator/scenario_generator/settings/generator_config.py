from functools import lru_cache
from pathlib import Path

from scenario_generator.settings import general, volume_profile

from pydantic_settings import BaseSettings


class ScenarioConfig(BaseSettings):
    vehicle_type_config_path: Path = general.ROOT_UTILS_PATH / "vehicles_types.xml"
    net_file_path: str = "net.net.xml"
    route_file_path: str = "routes.rou.xml"
    trip_file_path: str = "trips.trips.xml"
    volume_profile: dict[int, float] = volume_profile.traffic_volume_profile

    min_trip_distance_m: int = 1500
    max_trip_distance_m: int = 30000
    prefix: str = "vehicle"

    # should be the same as in vehicle_types.xml
    vehicle_type: str = "vehicle_distribution"


@lru_cache(maxsize=1)
def get_scenario_conf() -> ScenarioConfig:
    return ScenarioConfig()
