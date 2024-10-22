from functools import lru_cache

from h2mob.settings import general


class SimulationConfig(general.GeneralConfig):
    fuel_threshold_liters: int = 20
    hydrogen_vehicle_colour: tuple[int, int, int, int] = (255, 0, 0, 255)
    petrol_vehicle_colour: tuple[int, int, int, int] = (0, 255, 0, 255)


@lru_cache(maxsize=1)
def get_simulation_config() -> SimulationConfig:
    return SimulationConfig()
