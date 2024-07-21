from functools import lru_cache

from pydantic_settings import BaseSettings


class SimulationConfig(BaseSettings):
    sumocfg_file: str = "osm.sumocfg"
    routes_file: str = "routes.rou.xml"
    fuel_threshold_liters: int = 10
    hydrogen_vehicle_colour: tuple[int, int, int, int]= (255,0,0,255)
    petrol_vehicle_colour: tuple[int, int, int, int] = (0,255,0,255)


@lru_cache(maxsize=1)
def get_simulation_config() -> SimulationConfig:
    return SimulationConfig()
