from abc import ABC, abstractmethod
from logging import Logger
from pathlib import Path

from h2mob.settings.simulation import (
    GasStation,
    SimulationConfig,
    VehicleConfig,
)

import traci


class Service(ABC):
    @abstractmethod
    def run(self) -> None:
        ...


class Step(traci.StepListener):
    @abstractmethod
    def __init__(self, config: SimulationConfig) -> None:
        ...


class Client(ABC):
    @abstractmethod
    def route_to_nearest_gas_station(
        self, vehicle_id: str, gas_stations: list[GasStation], stop_duration_sec: int
    ) -> None:
        ...

    @abstractmethod
    def get_loaded_vehicles_ids(self) -> list[str]:
        ...

    @abstractmethod
    def get_vehicles_ids_in_simulation(self) -> list[str]:
        ...

    @abstractmethod
    def get_tank_level_liters(self, vehicle_id: str) -> float:
        ...

    @abstractmethod
    def set_vehicle_type(self, vehicle_id: str, vehicle_type: VehicleConfig) -> None:
        ...


class SumoClient(Client):
    def route_to_nearest_gas_station(
        self, vehicle_id: str, gas_stations: list[GasStation], stop_duration_sec: int
    ) -> None:
        vehicle_lane = traci.vehicle.getLaneID(vehicle_id)
        vehicle_edge = traci.lane.getEdgeID(vehicle_lane)

        def distance_to_station(gas_station: GasStation) -> GasStation:
            return traci.simulation.getDistanceRoad(
                edgeID1=vehicle_edge,
                pos1=0,
                edgeID2=gas_station.lane,
                pos2=0,
                isDriving=True,
            )

        nearest_gas_station = min(gas_stations, key=distance_to_station)

        traci.vehicle.setVia(vehicle_id, nearest_gas_station.lane)
        traci.vehicle.rerouteTraveltime(vehicle_id)
        traci.vehicle.setChargingStationStop(
            vehicle_id,
            nearest_gas_station.id,
            stop_duration_sec,
        )

    def get_loaded_vehicles_ids(self) -> list[str]:
        return traci.simulation.getLoadedIDList()

    def get_vehicles_ids_in_simulation(self) -> list[str]:
        return traci.vehicle.getIDList()

    def get_tank_level_liters(self, vehicle_id: str) -> float:
        tank_mg = int(traci.vehicle.getParameter(vehicle_id, "actualBatteryCapacity"))
        return tank_mg / 748_900  # mg in liter

    def set_vehicle_type(self, vehicle_id: str, vehicle_type: VehicleConfig) -> None:
        ...


class ConfigureVehicle(Step):
    def __init__(self, config: SimulationConfig) -> None:
        self.config = config

    def step(self, t: int) -> bool:
        print("configuration step listener")
        return True


class VehicleRouter(traci.StepListener):
    def __init__(self, config: SimulationConfig) -> None:
        self.config = config

    def step(self, t: int) -> bool:
        print("routing step listener")
        return True


class SimulationService(Service):
    listeners: tuple[type[Step], ...] = (
        VehicleRouter,
        ConfigureVehicle,
    )

    def __init__(
        self, logger: Logger, config: SimulationConfig, scenario_path: Path
    ) -> None:
        self.config = config
        self.scenario_path = scenario_path
        self.logger = logger

    def run(self) -> None:
        try:
            self.simulation_loop()
        except KeyboardInterrupt:
            self.logger.warning("Simulation inerrupted by user")
        finally:
            self.logger.info("Simulation has been completed")
            traci.close()

    def add_simulation_listeners(self) -> None:
        for listener_type in self.listeners:
            listener = listener_type(self.config)
            traci.addStepListener(listener)

    def simulation_loop(self) -> None:
        sumocfg_file = self.scenario_path / self.config.sumocfg_file
        traci.start(["sumo-gui", "-c", sumocfg_file])

        self.add_simulation_listeners()

        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()


def get_simulation_service(
    logger: Logger, config: SimulationConfig, scenario_path: Path
) -> Service:
    return SimulationService(logger=logger, config=config, scenario_path=scenario_path)
