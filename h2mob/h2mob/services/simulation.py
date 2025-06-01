import random

from abc import ABC, abstractmethod
from enum import Enum
from logging import Logger
from pathlib import Path
from typing import cast
from xml.etree import ElementTree

from h2mob.settings.simulation import SimulationConfig

import traci  # type: ignore

from pydantic import BaseModel


class FuelType(Enum):
    petrol = 0
    hydrogen = 1


class GasStation(BaseModel):
    id: str
    lane: str
    fuel_type: FuelType


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


FuelStations = list[GasStation]
HydrogenStations = list[GasStation]


class ScenarioConfig(BaseModel):
    fuel_stations: FuelStations
    hydrogen_stations: HydrogenStations
    vehicles: dict[str, Vehicle]


class Service(ABC):
    @abstractmethod
    def run(self) -> None: ...


class SumoClient:
    mg_in_liters: int = 748_900
    configured_vehicles: set[str] = set()

    def __init__(self, logger: Logger) -> None:
        self.logger: Logger = logger

    def route_to_nearest_gas_station(
        self, vehicle_id: str, gas_stations: list[GasStation], stop_duration_sec: int
    ) -> None:
        vehicle_lane: str = cast(str, traci.vehicle.getLaneID(vehID=vehicle_id))
        vehicle_edge: str = cast(str, traci.lane.getEdgeID(laneID=vehicle_lane))

        def distance_to_station(gas_station: GasStation) -> GasStation:
            return traci.simulation.getDistanceRoad(  # type: ignore
                edgeID1=vehicle_edge,
                pos1=0,
                edgeID2=gas_station.lane,
                pos2=0,
                isDriving=True,
            )

        nearest_gas_station: GasStation = min(gas_stations, key=distance_to_station)  # type: ignore

        traci.vehicle.setVia(vehID=vehicle_id, edgeList=nearest_gas_station.lane)
        traci.vehicle.rerouteTraveltime(vehID=vehicle_id)
        traci.vehicle.setChargingStationStop(
            vehID=vehicle_id,
            stopID=nearest_gas_station.id,
            duration=stop_duration_sec,
        )
        self.logger.info(f"Routing {vehicle_id=} to {nearest_gas_station=}")

    def get_loaded_vehicles_ids(self) -> list[str]:
        return traci.simulation.getLoadedIDList()  # type: ignore

    def get_vehicles_ids_in_simulation(self) -> list[str]:
        return traci.vehicle.getIDList()

    def get_tank_level_liters(self, vehicle_id: str) -> float:
        tank_mg_response: str = cast(
            str,
            traci.vehicle.getParameter(
                objectID=vehicle_id, key="device.battery.actualBatteryCapacity"
            ),
        )
        tank_mg = float(tank_mg_response)
        return tank_mg / self.mg_in_liters  # mg in liter

    def set_vehicle_type(self, vehicle_id: str, vehicle_type: Vehicle) -> None:
        vehicle_parameters: dict = {
            "device.battery.actualBatteryCapacity": vehicle_type.tank_liters
            * self.mg_in_liters,
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
            "vehicleFuelType": vehicle_type.fuel_type.name,
        }

        for key, value in vehicle_parameters.items():
            traci.vehicle.setParameter(vehicle_id, key, value)

        traci.vehicle.setColor(vehicle_id, vehicle_type.colour)
        self.configured_vehicles.add(vehicle_id)

    def set_vehicle_class_to_custom1(self) -> None:
        vehicle_types: list[str] = traci.vehicletype.getIDList()  # type: ignore
        for vehicle_type in vehicle_types:
            traci.vehicletype.setVehicleClass(typeID=vehicle_type, clazz="custom1")

    def get_configured_vehicles(self) -> set[str]:
        return self.configured_vehicles


class Step(traci.StepListener):
    def __init__(
        self,
        client: SumoClient,
        logger: Logger,
        simulation_config: SimulationConfig,
        scenario_config: ScenarioConfig,
    ) -> None:
        self.logger: Logger = logger
        self.simulation_config: SimulationConfig = simulation_config
        self.scenario_config: ScenarioConfig = scenario_config
        self.client: SumoClient = client


class ConfigureVehicle(Step):
    def step(self, t: int = 0) -> bool:  # type: ignore
        loaded_vehicle_ids: list[str] = self.client.get_loaded_vehicles_ids()

        for vehicle_id in loaded_vehicle_ids:
            vehicle_type: Vehicle = self.scenario_config.vehicles[vehicle_id]
            self.client.set_vehicle_type(
                vehicle_id=vehicle_id,
                vehicle_type=vehicle_type,
            )

        return True


class VehicleRouter(Step):
    routed_vehicles: set = set()

    def step(self, t: int = 0) -> bool:  # type: ignore
        vehicles: set[str] = set(self.client.get_vehicles_ids_in_simulation())
        configured_vehicles: set[str] = self.client.get_configured_vehicles()
        configured_vehicles_in_simulation: set[str] = configured_vehicles & vehicles
        vehicles_to_check: set[str] = (
            configured_vehicles_in_simulation - self.routed_vehicles
        )
        vehicles_tank_level: dict[str, float] = {
            vehicle_id: self.client.get_tank_level_liters(vehicle_id=vehicle_id)
            for vehicle_id in vehicles_to_check
        }
        vehicles_to_reroute: list[str] = [
            vehicle_id
            for vehicle_id, tank_level_l in vehicles_tank_level.items()
            if tank_level_l < self.simulation_config.fuel_threshold_liters
        ]

        for vehicle_id in vehicles_to_reroute:
            vehicle_type: Vehicle = self.scenario_config.vehicles[vehicle_id]
            if vehicle_type.fuel_type == FuelType.petrol:
                charging_station = self.scenario_config.fuel_stations
            else:
                charging_station = self.scenario_config.hydrogen_stations

            self.client.route_to_nearest_gas_station(
                vehicle_id=vehicle_id,
                gas_stations=charging_station,
                stop_duration_sec=vehicle_type.charging_duration_seconds,
            )

        self.routed_vehicles.update(vehicles_to_reroute)

        return True


class SimulationService(Service):
    listeners: tuple[type[Step], ...] = (
        VehicleRouter,
        ConfigureVehicle,
    )

    def __init__(
        self,
        logger: Logger,
        simulation_config: SimulationConfig,
        scenario_config: ScenarioConfig,
        scenario_path: Path,
        output_folder: Path,
    ) -> None:
        self.simulation_config: SimulationConfig = simulation_config
        self.scenario_config: ScenarioConfig = scenario_config
        self.scenario_path: Path = scenario_path
        self.output_folder = output_folder
        self.logger: Logger = logger
        self.client = SumoClient(logger=logger)

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
            traci.addStepListener(listener=listener)

    def simulation_loop(self) -> None:
        sumocfg_file: Path = self.scenario_path.joinpath(
            self.simulation_config.sumocfg_file_path
        )
        traci.start(
            cmd=[
                "sumo",
                "-c",
                sumocfg_file,
                "--fcd-output",
                self.output_folder / "fcd.out.xml",
                "--fcd-output.acceleration",
                "--statistic-output",
                self.output_folder / "statistics.out.xml",
                "--chargingstations-output",
                self.output_folder / "chargingstations.out.xml",
                "--summary-output",
                self.output_folder / "summary.out.xml",
                "--battery-output.precision",
                "4",
                "--battery-output",
                self.output_folder / "battery.out.xml",
            ]
        )
        self.client.set_vehicle_class_to_custom1()
        self.add_simulation_listeners()

        while traci.simulation.getMinExpectedNumber() > 0:  # type: ignore
            traci.simulationStep()


class ScenarioParser:
    def __init__(
        self,
        simulation_config: SimulationConfig,
        scenario_path: Path,
        hydrogen_stations: set[str],
        percent_of_hydrogen_cars: float,
    ) -> None:
        self.percent_of_hydrogen_cars = percent_of_hydrogen_cars
        self.scenario_path = scenario_path
        self.simulation_config = simulation_config
        self.hydrogen_stations = hydrogen_stations

    def get_scenario_config(self) -> ScenarioConfig:
        vehicle_ids = self.get_vehicle_ids()
        vehicles = self.generate_vehicle_configs(vehicle_ids)
        fuel_stations, hydrogen_stations = self.get_fuel_stations()
        return ScenarioConfig(
            hydrogen_stations=hydrogen_stations,
            fuel_stations=fuel_stations,
            vehicles=vehicles,
        )

    def get_vehicle_ids(self) -> list[str]:
        routes = self.scenario_path / self.simulation_config.route_file_path
        routers_root = ElementTree.parse(routes)
        return [vehicle.attrib["id"] for vehicle in routers_root.findall("vehicle")]  # type: ignore

    def generate_vehicle_configs(self, vehicle_ids: list[str]) -> dict[str, Vehicle]:
        vehicles_configs: dict[str, Vehicle] = {}

        for vehicle_id in vehicle_ids:
            fuel_type = FuelType.petrol
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

    def get_fuel_stations(self) -> tuple[FuelStations, HydrogenStations]:
        gas_stations_path = (
            self.scenario_path / self.simulation_config.charging_stations_path
        )
        stations_root = ElementTree.parse(gas_stations_path)
        hydrogen_stations: list[GasStation] = []
        fuel_station: list[GasStation] = []

        for station in stations_root.findall("chargingStation"):
            if station.attrib["id"] in self.hydrogen_stations:
                hydrogen_stations.append(
                    GasStation(
                        id=station.attrib["id"],
                        lane=station.attrib["lane"].split("_")[0],
                        fuel_type=FuelType.hydrogen,
                    )
                )
            else:
                fuel_station.append(
                    GasStation(
                        id=station.attrib["id"],
                        lane=station.attrib["lane"].split("_")[0],
                        fuel_type=FuelType.petrol,
                    )
                )

        return fuel_station, hydrogen_stations


def get_simulation_service(
    logger: Logger,
    simulation_config: SimulationConfig,
    hydrogen_stations: set[str],
    scenario_path: Path,
    percent_of_hydrogen_cars: float,
) -> Service:
    scenario_parser = ScenarioParser(
        simulation_config=simulation_config,
        scenario_path=scenario_path,
        hydrogen_stations=hydrogen_stations,
        percent_of_hydrogen_cars=percent_of_hydrogen_cars,
    )
    scenario_config = scenario_parser.get_scenario_config()
    out_folder_name = f"out_hydrogen_cars_{percent_of_hydrogen_cars}_hydrogen_stations_{'_'.join(hydrogen_stations)}"  # noqa
    output_folder = scenario_path / out_folder_name
    output_folder.mkdir(exist_ok=False)
    return SimulationService(
        logger=logger,
        simulation_config=simulation_config,
        output_folder=output_folder,
        scenario_config=scenario_config,
        scenario_path=scenario_path,
    )
