import random

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


class GasStation(BaseModel):
    id: str
    lane: str


class VehicleConfig(BaseModel):
    charging_duration_seconds: int = 5 * 60  # 5 mins

    # sumo specific config
    tank_liters: int
    mass_kg: int
    front_surface_area: float
    air_drag_coefficient: float
    constant_power_intake: int
    internal_moment_of_inertia: float
    radial_drag_coefficient: float
    roll_drag_coefficient: float
    propulsion_efficiency: float
    recuperatoin_efficiency: float = 0.0
    stopping_threshold: float


class SimulationConfig(BaseModel):
    fuel_stations: list[GasStation]
    hydrogen_stations: list[GasStation]
    vehicle_configs: list[VehicleConfig]

    sumocfg_file: str = "osm.sumocfg"

    fuel_threshold_liters: int = 10
    hydrogen_vehicle_colour: str = "red"
    petrol_vehicle_colour: str = "blue"


# TODO: ideally we want to have a config file where we specify rand
def generate_vehicle_configs() -> list[VehicleConfig]:
    vehicle_configs = [
        VehicleConfig(
            charging_duration_seconds=random.randint(5 * 60, 15 * 60),
            tank_liters=random.randint(40, 80),
            mass_kg=random.randint(1500, 2200),
            # change to rand
            front_surface_area=2.6,
            air_drag_coefficient=0.35,
            constant_power_intake=100,
            internal_moment_of_inertia=0.01,
            radial_drag_coefficient=0.01,
            roll_drag_coefficient=0.01,
            propulsion_efficiency=0.98,
            recuperatoin_efficiency=0.0,
            stopping_threshold=0.1,
        )
        for _ in range(10)
    ]
    return vehicle_configs


# TODO: extract data from scenario file
def get_fuel_stations(scenario_path: Path) -> list[GasStation]:
    return [GasStation(id=f"{i}", lane=f"lane_{i}") for i in range(10)]


@lru_cache(maxsize=1)
def get_simulation_config(scenario_path: Path) -> SimulationConfig:
    return SimulationConfig(
        vehicle_configs=generate_vehicle_configs(),
        fuel_stations=get_fuel_stations(scenario_path=scenario_path),
        hydrogen_stations=get_fuel_stations(scenario_path=scenario_path),
    )
