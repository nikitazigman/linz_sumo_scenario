import random

from abc import ABC, abstractmethod
from enum import Enum
from logging import Logger
from pathlib import Path
from xml.etree import ElementTree

from h2mob.settings.simulation import SimulationConfig

import traci

from pydantic import BaseModel


class GasStation(BaseModel):
    id: str
    lane: str


class FuelType(Enum):
    petrol = 0
    hydrogen = 1


class Vehicle(BaseModel):
    colour: tuple[int, int, int, int]  # RGBA
    fuel_type: FuelType
    charging_duration_seconds: int = 5 * 60  # 5 mins
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


class ScenarioConfig(BaseModel):
    # fuel_stations: list[GasStation]
    # hydrogen_stations: list[GasStation]
    vehicles: dict[str, Vehicle]


class Service(ABC):
    @abstractmethod
    def run(self) -> None:
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
    def set_vehicle_type(self, vehicle_id: str, vehicle_type: Vehicle) -> None:
        ...


class SumoClient(Client):
    mg_in_liters: int = 748_900

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
        return tank_mg / self.mg_in_liters  # mg in liter

    def set_vehicle_type(self, vehicle_id: str, vehicle_type: Vehicle) -> None:
        vehicle_parameters: dict = {
            "actualBatteryCapacity": vehicle_type.tank_liters * self.mg_in_liters,
            "vehicleMass": vehicle_type.mass_kg,
            "frontSurfaceArea": vehicle_type.front_surface_area,
            "airDragCoefficient": vehicle_type.air_drag_coefficient,
            "constantPowerIntake": vehicle_type.constant_power_intake,
            "internalMomentOfInertia": vehicle_type.internal_moment_of_inertia,
            "radialDragCoefficient": vehicle_type.radial_drag_coefficient,
            "rollDragCoefficient": vehicle_type.roll_drag_coefficient,
            "propulsionEfficiency": vehicle_type.propulsion_efficiency,
            "recuperationEfficiency": vehicle_type.recuperatoin_efficiency,
            "stoppingThreshold": vehicle_type.stopping_threshold,
        }

        for key, value in vehicle_parameters.items():
            traci.vehicle.setParameter(vehicle_id, key, value)

        traci.vehicle.setColor(vehicle_id, vehicle_type.colour)


class Step(traci.StepListener):
    def __init__(
        self,
        client: Client,
        logger: Logger,
        simulation_config: SimulationConfig,
        scenario_config: ScenarioConfig,
    ) -> None:
        self.logger = logger
        self.simulation_config = simulation_config
        self.scenario_config = scenario_config
        self.client = client


class ConfigureVehicle(Step):
    configured_vehicles: set = set()

    def step(self, t: int) -> bool:
        loaded_vehicle_ids = self.client.get_loaded_vehicles_ids()

        for vehicle_id in loaded_vehicle_ids:
            vehicle_type = self.scenario_config.vehicles[vehicle_id]
            self.client.set_vehicle_type(vehicle_id, vehicle_type)

        self.configured_vehicles.update(loaded_vehicle_ids)
        return True


class VehicleRouter(Step):
    def step(self, t: int) -> bool:
        return True


class SimulationService(Service):
    listeners: tuple[type[Step], ...] = (
        VehicleRouter,
        ConfigureVehicle,
    )
    client: Client = SumoClient()

    def __init__(
        self,
        logger: Logger,
        simulation_config: SimulationConfig,
        scenario_config: ScenarioConfig,
        scenario_path: Path,
    ) -> None:
        self.simulation_config = simulation_config
        self.scenario_config = scenario_config
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
            listener = listener_type(
                scenario_config=self.scenario_config,
                simulation_config=self.simulation_config,
                client=self.client,
                logger=self.logger,
            )
            traci.addStepListener(listener)

    def simulation_loop(self) -> None:
        sumocfg_file = self.scenario_path / self.simulation_config.sumocfg_file
        traci.start(["sumo-gui", "-c", sumocfg_file])

        self.add_simulation_listeners()

        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()


class ScenarioParser:
    def __init__(
        self,
        simulation_config: SimulationConfig,
        scenario_path: Path,
        percent_of_hydrogen_cars: float,
    ) -> None:
        self.percent_of_hydrogen_cars = percent_of_hydrogen_cars
        self.scenario_path = scenario_path
        self.simulation_config = simulation_config

    def get_scenario_config(self) -> ScenarioConfig:
        vehicle_ids = self.get_vehicle_ids()
        vehicles = self.generate_vehicle_configs(vehicle_ids)

        return ScenarioConfig(
            # gas_stations=[],
            # fuel_stations=[],
            vehicles=vehicles,
        )

    def get_vehicle_ids(self) -> list[str]:
        routes = self.scenario_path / self.simulation_config.routes_file
        routers_root = ElementTree.parse(routes)
        return [vehicle.attrib["id"] for vehicle in routers_root.findall("vehicle")]  # type: ignore

    def generate_vehicle_configs(self, vehicle_ids: list[str]) -> dict[str, Vehicle]:
        vehicles_configs: dict[str, Vehicle] = {}

        for vehicle_id in vehicle_ids:
            fuel_type = FuelType.hydrogen
            colour = self.simulation_config.petrol_vehicle_colour

            if random.random() < self.percent_of_hydrogen_cars:  # replace to user input
                fuel_type = FuelType.hydrogen
                colour = self.simulation_config.hydrogen_vehicle_colour

            vehicles_configs[vehicle_id] = Vehicle(
                colour=colour,
                fuel_type=fuel_type,
                charging_duration_seconds=random.randint(5 * 60, 15 * 60),
                tank_liters=random.randint(20, 45),
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

        return vehicles_configs

    # TODO: extract data from scenario file
    def get_fuel_stations(self) -> tuple[list[GasStation], list[GasStation]]:
        return [GasStation(id="1", lane="lane")], [GasStation(id="1", lane="lane")]


def get_simulation_service(
    logger: Logger,
    simulation_config: SimulationConfig,
    scenario_path: Path,
    percent_of_hydrogen_cars: float,
) -> Service:
    scenario_parser = ScenarioParser(
        simulation_config=simulation_config,
        scenario_path=scenario_path,
        percent_of_hydrogen_cars=percent_of_hydrogen_cars,
    )
    scenario_config = scenario_parser.get_scenario_config()
    return SimulationService(
        logger=logger,
        simulation_config=simulation_config,
        scenario_config=scenario_config,
        scenario_path=scenario_path,
    )
