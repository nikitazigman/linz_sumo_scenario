from functools import lru_cache

from src.utils.scenario_parser import ISumoScenarioParser

from pydantic import BaseModel


class FuelStationSchema(BaseModel):
    id: str
    lane: str


class ScenarioConfig(BaseModel):
    h_vehicles_ids: set[str]
    fuel_stations: list[FuelStationSchema]

    fuel_threshold_liters: int = 10
    max_tank_capacity_litres: int = 50
    charging_duration_seconds: int = 5 * 60  # 5 minutes


@lru_cache(maxsize=1)
def get_scenario_config(parser: ISumoScenarioParser) -> ScenarioConfig:
    h_vehicles_ids = parser.get_h_vehicle_ids()
    fuel_stations = parser.get_fuel_stations()

    scenario_config = ScenarioConfig(
        h_vehicles_ids=h_vehicles_ids, fuel_stations=fuel_stations
    )

    return scenario_config
