import random

from abc import ABC, abstractmethod

from src.storages.simulation import ISimulationStorage

from loguru import logger


class IVehicleService(ABC):
    @abstractmethod
    def get_loaded_h_vehicle_ids(self) -> set[str]:
        ...

    @abstractmethod
    def get_h_vehicles_in_simulation(self) -> set[str]:
        ...

    @abstractmethod
    def assign_tank_level(self, h_vehicles: set[str]) -> None:
        """Assigns a random tank level to each h-vehicle."""

    @abstractmethod
    def fuel_level_handler(self, h_vehicles: set[str]) -> set[str]:
        """Reroutes h-vehicle to the nearest gas
        station if fuel level is below a threshold.
        """

    @abstractmethod
    def filter_by_fuel_threshold(self, h_vehicles: set[str]) -> set[str]:
        ...

    @abstractmethod
    def reroute_via_nearest_fuel_station(self, vehicles_ids: set[str]) -> None:
        ...


class VehicleService(IVehicleService):
    def __init__(self, simulation_storage: ISimulationStorage):
        self.sim_storage = simulation_storage

    def assign_tank_level(self, h_vehicles: set[str]) -> None:
        for vehicle_id in h_vehicles:
            tank_level_l = self._get_random_tank_level(vehicle_id)
            self.sim_storage.set_vehicle_tank_level(vehicle_id, tank_level_l)

    def fuel_level_handler(self, h_vehicles: set[str]) -> set[str]:
        h_vehicles_with_low_fuel = self.filter_by_fuel_threshold(h_vehicles)

        if h_vehicles_with_low_fuel:
            self.reroute_via_nearest_fuel_station(h_vehicles_with_low_fuel)

        return h_vehicles_with_low_fuel

    def get_loaded_h_vehicle_ids(self) -> set[str]:
        loaded_vehicles = self.sim_storage.get_loaded_vehicles_ids()
        loaded_h_vehicles = self._extract_h_vehicles(loaded_vehicles)

        return loaded_h_vehicles

    def get_h_vehicles_in_simulation(self) -> set[str]:
        loaded_vehicles = self.sim_storage.get_vehicles_ids_in_sim()
        h_vehicles_in_simulation = self._extract_h_vehicles(loaded_vehicles)

        return h_vehicles_in_simulation

    def filter_by_fuel_threshold(self, h_vehicles: set[str]) -> set[str]:
        fuel_threshold = self.sim_storage.get_fuel_threshold_liters()

        vehicles_with_low_fuel = {
            vehicle_id
            for vehicle_id in h_vehicles
            if self.sim_storage.get_tank_level_l(vehicle_id) < fuel_threshold
        }

        return vehicles_with_low_fuel

    def reroute_via_nearest_fuel_station(self, vehicles_ids: set[str]) -> None:
        duration = self.sim_storage.get_charging_duration_seconds()

        for vehicle_id in vehicles_ids:
            self._reroute_vehicle_via_nearest_fuel_station(
                vehicle_id, duration
            )

    def _extract_h_vehicles(self, vehicles_ids: set[str]) -> set[str]:
        h_vehicles = self.sim_storage.get_h_vehicles_ids()
        return h_vehicles.intersection(vehicles_ids)

    def _get_random_tank_level(self, vehicle_id: str) -> int:
        tank_capacity_l = self.sim_storage.get_tank_capacity_litres()
        min_tank_level_l = int(tank_capacity_l * 0.1)
        return random.randint(min_tank_level_l, tank_capacity_l)

    def _reroute_vehicle_via_nearest_fuel_station(
        self, vehicle_id: str, duration_sec: int
    ) -> None:
        nearest_station = self.sim_storage.get_nearest_fuel_station(vehicle_id)

        self.sim_storage.reroute_via_point(vehicle_id, nearest_station.lane)
        self.sim_storage.set_charging_stop(
            vehicle_id, nearest_station.id, duration_sec
        )

        logger.info(
            f"Rerouting {vehicle_id} vehicle "
            f"via nearest fuel station {nearest_station}"
        )


def get_vehicle_service(
    simulation_storage: ISimulationStorage,
) -> IVehicleService:
    return VehicleService(
        simulation_storage=simulation_storage,
    )
