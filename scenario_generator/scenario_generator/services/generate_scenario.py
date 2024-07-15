import subprocess

from abc import ABC, abstractmethod
from pathlib import Path

from scenario_generator.settings import generator_config

import rich


class Service(ABC):
    @abstractmethod
    def __init__(
        self,
        config: generator_config.ScenarioConfig,
        scenario: Path,
        total_vehicle_volume: int,
    ) -> None:
        ...

    @abstractmethod
    def generate_scenario(self) -> None:
        ...


class ScenarioGeneratorService(Service):
    def __init__(
        self,
        config: generator_config.ScenarioConfig,
        scenario: Path,
        total_vehicle_volume: int,
    ) -> None:
        self.net_file = scenario / config.net_file_path
        self.route_file = scenario / config.route_file_path
        self.trip_file = scenario / config.trip_file_path
        self.vehicle_type_file = config.vehicle_type_config_path
        self.total_vehicle = total_vehicle_volume

        self.trafic_profile = config.volume_profile
        self.start_time_sec = 0
        self.stop_time_sec = 24 * 3600
        self.min_distance_m = config.min_trip_distance_m
        self.max_distance_m = config.max_trip_distance_m
        self.prefix = config.prefix
        self.vehicle_type = config.vehicle_type

    def build_command(self, period: list[float]) -> str:
        period_str = ",".join([str(p) for p in period])
        command = (
            "python /opt/homebrew/share/sumo/tools/randomTrips.py "
            f"--net-file {self.net_file} "
            f"-o {self.trip_file} "
            f"""--trip-attributes="type='{self.vehicle_type_file}'" """
            f"--begin {self.start_time_sec} "
            f"--end {self.stop_time_sec} "
            f"-p {period_str} "
            f"--max-distance {self.max_distance_m} "
            f"--min-distance {self.min_distance_m} "
            f"--prefix {self.prefix} "
            f"--route-file {self.route_file} "
            f"--additional-files {self.vehicle_type_file} "
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

        for i in range(0, 24):
            t0, t1 = i * 3600, (i + 1) * 3600
            period = (t1 - t0) / self.trafic_profile[i]
            rounded_period = round(period, 2)
            periods.append(rounded_period)

        return periods

    def generate_scenario(self) -> None:
        periods: list[float] = self.compute_periods()
        command = self.build_command(period=periods)
        self.generate_random_traffic(command)


def get_scenario_generator_service(
    config: generator_config.ScenarioConfig,
    scenario: Path,
    total_vehicle_volume: int,
) -> Service:
    return ScenarioGeneratorService(
        config=config,
        scenario=scenario,
        total_vehicle_volume=total_vehicle_volume,
    )
