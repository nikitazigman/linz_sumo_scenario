import shutil
import subprocess

from abc import ABC, abstractmethod
from pathlib import Path

from h2mob.settings import generator_config
from h2mob.settings.general import ROOT_UTILS_PATH

import rich


class Service(ABC):
    @abstractmethod
    def __init__(
        self,
        config: generator_config.ScenarioConfig,
        net_file: Path,
        total_vehicle_volume: int,
    ) -> None:
        ...

    @abstractmethod
    def generate_scenario(self) -> None:
        ...


class ScenarioGeneratorService(Service):
    def __init__(
        self,
        scenario_name: str,
        config: generator_config.ScenarioConfig,
        net_file: Path,
        total_vehicle_volume: int,
    ) -> None:
        self.net_file = net_file
        self.scenario_name = scenario_name
        self.total_vehicle = total_vehicle_volume
        self.start_time_sec = 0
        self.stop_time_sec = 24 * 3600
        self.config = config

    def build_command(self, scenario: Path, period: list[float]) -> str:
        period_str = ",".join([str(p) for p in period])
        command = (
            "python /opt/homebrew/share/sumo/tools/randomTrips.py "
            f"--net-file {self.net_file} "
            f"-o {scenario / self.config.trip_file_path} "
            f"--begin {self.start_time_sec} "
            f"--end {self.stop_time_sec} "
            f"-p {period_str} "
            f"--max-distance {self.config.max_trip_distance_m} "
            f"--min-distance {self.config.min_trip_distance_m} "
            f"--prefix {self.config.prefix} "
            f"--route-file {scenario / self.config.route_file_path} "
            f"--random "
            "--validate "
            f"--verbose"
        )
        return command

    def generate_random_traffic(self, command: str) -> None:
        with subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ) as process:
            response = process.communicate()

        if process.returncode != 0:
            raise RuntimeError(
                "Error while generating random traffic:\n"
                f" {response[0].decode('utf-8')}\n"
                f" {response[1].decode('utf-8')}\n"
            )

        rich.print(
            f"Successfully generated random traffic: \n{response[0].decode('utf-8')}"
        )
        return None

    def compute_periods(self) -> list[float]:
        periods: list[float] = []

        for hour in range(0, 24):
            t0, t1 = hour * 3600, (hour + 1) * 3600
            period = (t1 - t0) / self.config.volume_profile[hour]
            rounded_period = round(period, 2)
            periods.append(rounded_period)

        return periods

    def build_scenario_directory(self) -> Path:
        scenario_path = ROOT_UTILS_PATH.parent / f"scenarios/{self.scenario_name}"

        if scenario_path.exists():
            shutil.rmtree(scenario_path)

        shutil.copytree(src=self.config.template_path, dst=scenario_path)
        shutil.copy(src=self.net_file, dst=scenario_path / "osm.net.xml")

        scenario_path.joinpath("out").mkdir()
        return scenario_path

    def generate_scenario(self) -> None:
        scenario = self.build_scenario_directory()
        periods: list[float] = self.compute_periods()
        command = self.build_command(period=periods, scenario=scenario)
        self.generate_random_traffic(command)


def get_scenario_generator_service(
    scenario_name: str,
    config: generator_config.ScenarioConfig,
    net_file: Path,
    total_vehicle_volume: int,
) -> Service:
    return ScenarioGeneratorService(
        scenario_name=scenario_name,
        config=config,
        net_file=net_file,
        total_vehicle_volume=total_vehicle_volume,
    )
