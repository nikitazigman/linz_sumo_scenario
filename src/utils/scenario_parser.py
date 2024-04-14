from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


class ISumoScenarioParser(ABC):
    @abstractmethod
    def get_h_vehicle_ids(self) -> tuple[str, ...]:
        ...

    @abstractmethod
    def get_fuel_stations(self) -> tuple[dict[str, Any], ...]:
        ...


class SumoScenarioParser(ISumoScenarioParser):
    def __init__(self, sumo_config: Path):
        scenario_folder = sumo_config.parent

        config_root = ElementTree.parse(sumo_config).getroot()
        input_element = config_root.find("input")
        if input_element is None:
            raise ValueError("input element not found")

        route_files_element = input_element.find("route-files")
        add_files_element = input_element.find("additional-files")

        if route_files_element is None:
            raise ValueError("route-files element not found")

        if add_files_element is None:
            raise ValueError("additional-files element not found")

        route_file = scenario_folder / route_files_element.attrib["value"]
        stations_file = scenario_folder / add_files_element.attrib["value"]

        self.station_root = ElementTree.parse(stations_file).getroot()
        self.route_root = ElementTree.parse(route_file).getroot()

    def get_h_vehicle_ids(self) -> tuple[str, ...]:
        all_vehicles = self.route_root.findall("vehicle")
        h_vehicles = [
            vehicle.attrib["id"]
            for vehicle in all_vehicles
            if vehicle.attrib["type"] == "h-vehicle"
        ]
        return tuple(h_vehicles)

    def get_fuel_stations(self) -> tuple[dict[str, Any], ...]:
        fuel_stations = self.station_root.findall("chargingStation")
        stations = [
            {
                "id": station.attrib["id"],
                "lane": station.attrib["lane"].split("_")[0],
            }
            for station in fuel_stations
        ]
        return tuple(stations)


def get_sumo_scenario_parser(sumo_config: Path) -> ISumoScenarioParser:
    return SumoScenarioParser(sumo_config)
