from abc import ABC, abstractmethod

from src.configs.scenario_config import FuelStationSchema, ScenarioConfig

import traci


class ISimulationStorage(ABC):
    @abstractmethod
    def get_nearest_fuel_station(self, vehicle_id: str) -> FuelStationSchema:
        ...

    @abstractmethod
    def get_charging_duration_seconds(self) -> int:
        ...

    @abstractmethod
    def get_tank_capacity_litres(self) -> int:
        ...

    @abstractmethod
    def get_fuel_threshold_liters(self) -> int:
        ...

    @abstractmethod
    def get_step(self) -> int:
        ...

    @abstractmethod
    def get_h_vehicles_ids(self) -> set[str]:
        ...

    @abstractmethod
    def get_fuel_stations(self) -> list[FuelStationSchema]:
        ...

    @abstractmethod
    def get_loaded_vehicles_ids(self) -> set[str]:
        ...

    @abstractmethod
    def get_vehicles_ids_in_sim(self) -> set[str]:
        ...

    @abstractmethod
    def get_tank_level_l(self, vehicle_id: str) -> float:
        ...

    @abstractmethod
    def set_vehicle_tank_level(
        self, vehicle_id: str, tank_level_litres: int
    ) -> None:
        ...

    @abstractmethod
    def reroute_via_point(self, vehicle_id: str, lane_id: str) -> None:
        ...

    @abstractmethod
    def set_charging_stop(
        self, vehicle_id: str, charging_station_id: str, duration: int
    ) -> None:
        ...

    @abstractmethod
    def subscribe_to_simulation_data(self) -> None:
        ...


class SimulationStorage(ISimulationStorage):
    _fuel_level_property = "actualBatteryCapacity"
    _mg_in_litres = 748_900

    def __init__(self, sumo_client: traci, scenario_config: ScenarioConfig):
        self.sumo_client = sumo_client
        self.scenario_config = scenario_config

    def get_nearest_fuel_station(self, vehicle_id: str) -> FuelStationSchema:
        vehicle_lane = self.sumo_client.vehicle.getLaneID(vehicle_id)
        vehicle_edge = self.sumo_client.lane.getEdgeID(vehicle_lane)
        fuel_stations = self.get_fuel_stations()

        def get_distance_to_station(station: FuelStationSchema) -> float:
            return self.sumo_client.simulation.getDistanceRoad(
                edgeID1=vehicle_edge,
                pos1=0,
                edgeID2=station.lane,
                pos2=0,
                isDriving=True,
            )

        nearest_station = min(fuel_stations, key=get_distance_to_station)

        return nearest_station

    def get_charging_duration_seconds(self) -> int:
        return self.scenario_config.charging_duration_seconds

    def get_tank_capacity_litres(self) -> int:
        return self.scenario_config.max_tank_capacity_litres

    def get_fuel_threshold_liters(self) -> int:
        return self.scenario_config.fuel_threshold_liters

    def get_step(self) -> int:
        return self.sumo_client.simulation.getTime()

    def get_fuel_stations(self) -> list[FuelStationSchema]:
        return self.scenario_config.fuel_stations

    def get_loaded_vehicles_ids(self) -> set[str]:
        return set(self.sumo_client.simulation.getLoadedIDList())

    def get_vehicles_ids_in_sim(self) -> set[str]:
        return set(self.sumo_client.vehicle.getIDList())

    def get_tank_level_l(self, vehicle_id: str) -> float:
        tank_level_mg = int(
            self.sumo_client.vehicle.getParameter(
                vehicle_id, self._fuel_level_property
            )
        )

        return tank_level_mg / self._mg_in_litres

    def get_h_vehicles_ids(self) -> set[str]:
        return self.scenario_config.h_vehicles_ids

    def set_vehicle_tank_level(
        self, vehicle_id: str, tank_level_litres: int
    ) -> None:
        tank_level_mg = tank_level_litres * self._mg_in_litres

        self.sumo_client.vehicle.setParameter(
            vehicle_id, self._fuel_level_property, tank_level_mg
        )

    def reroute_via_point(self, vehicle_id: str, lane_id: str) -> None:
        self.sumo_client.vehicle.setVia(vehicle_id, lane_id)
        self.sumo_client.vehicle.rerouteTraveltime(vehicle_id)

    def set_charging_stop(
        self, vehicle_id: str, charging_station_id: str, duration: int
    ) -> None:
        self.sumo_client.vehicle.setChargingStationStop(
            vehicle_id, charging_station_id, duration
        )

    def subscribe_to_simulation_data(self) -> None:
        ...
        # self.sumo_client.simulation.subscribe(self._simulation_subscriptions)

        # for vehicle_id in self.scenario_config.h_vehicles_ids:
        #     self.sumo_client.vehicle.subscribe(
        #         vehicle_id, self._vehicle_subscriptions
        #     )


def get_simulation_storage(
    sumo_client: traci, scenario_config: ScenarioConfig
) -> ISimulationStorage:
    return SimulationStorage(sumo_client, scenario_config)
