import shutil
import subprocess

from abc import ABC, abstractmethod
from logging import Logger
from pathlib import Path

from h2mob.settings import generator_config

import rich


class Service(ABC):
    @abstractmethod
    def __init__(
        self,
        config: generator_config.ScenarioConfig,
        charging_station_file: Path,
        net_file: Path,
        total_vehicle_volume: int,
        logger: Logger,
    ) -> None: ...

    @abstractmethod
    def generate_scenario(self) -> None: ...


class ScenarioGeneratorService(Service):
    def __init__(
        self,
        charging_station_file: Path,
        scenario_path: Path,
        config: generator_config.ScenarioConfig,
        net_file: Path,
        total_vehicle_volume: int,
        logger: Logger,
    ) -> None:
        self.net_file: Path = net_file
        self.charging_station_file: Path = charging_station_file
        self.scenario_path: Path = scenario_path
        self.total_vehicle: int = total_vehicle_volume
        self.start_time_sec = 0
        self.stop_time_sec = 24 * 3600
        self.config: generator_config.ScenarioConfig = config
        self.logger: Logger = logger

    def build_random_trip_command(self, period: list[float]) -> str:
        period_str = ",".join([str(p) for p in period])
        script_path = self.config.sumo_home / "tools/randomTrips.py"
        command = (
            f"python {script_path.absolute()} "
            f"--net-file {self.net_file} "
            f"-o {self.scenario_path / self.config.trip_file_path} "
            f"--begin {self.start_time_sec} "
            f"--end {self.stop_time_sec} "
            f"""--trip-attributes="type='{self.config.vehicle_type_name}'" """
            f"-p {period_str} "
            f"--max-distance {self.config.max_trip_distance_m} "
            f"--min-distance {self.config.min_trip_distance_m} "
            f"--prefix {self.config.prefix} "
            f"--additional-files {self.scenario_path / self.config.vehicle_type_path} "
            f"--random "
            f"--verbose"
        )
        return command

    def generate_random_trips(self, command: str) -> None:
        with subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        ) as process:
            if process.stdout is None:
                raise ValueError("stdout is None")
            if process.stderr is None:
                raise ValueError("sdterr is None")

            for line in process.stdout:
                rich.print(line)

            process.stdout.close()
            return_code = process.wait(timeout=10)  # 10 sec

        if return_code != 0:
            raise RuntimeError(
                f"Error while generating random traffic:\n{process.stderr.read()}"
            )

        rich.print("Successfully generated random traffic")
        return None

    def build_duarouter_command(self) -> str:
        command: str = (
            f"duarouter -n {self.scenario_path / self.config.net_path} "
            f"-t {self.scenario_path / self.config.trip_file_path} "
            f"-o {self.scenario_path / self.config.route_file_path} "
            f"--additional-files {self.scenario_path / self.config.vehicle_type_path} "
            "--routing-threads 20 "
            f"--ignore-errors "
            f"--verbose"
        )
        return command

    def convert_trips_to_routes(self, command: str) -> None:
        with subprocess.Popen(
            args=command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        ) as process:
            if process.stdout is None:
                raise ValueError("stdout is None")
            if process.stderr is None:
                raise ValueError("sdterr is None")

            for line in process.stdout:
                self.logger.info(line)

            process.stdout.close()
            return_code = process.wait(timeout=10)  # 10 sec

        if return_code != 0:
            raise RuntimeError(
                f"Error while generating random traffic:\n{process.stderr.read()}"
            )

        rich.print("Successfully convert trips to routes")
        return None

    def compute_periods(self) -> list[float]:
        periods: list[float] = []

        for hour in range(0, 24):
            t0, t1 = hour * 3600, (hour + 1) * 3600
            period = (t1 - t0) / (self.config.volume_profile[hour] * self.total_vehicle)
            rounded_period = round(period, 2)
            periods.append(rounded_period)

        return periods

    def build_scenario_directory(self) -> None:
        if self.scenario_path.exists():
            shutil.rmtree(self.scenario_path)

        shutil.copytree(src=self.config.template_path, dst=self.scenario_path)
        shutil.copy(
            src=self.net_file,
            dst=self.scenario_path / self.config.net_path,
        )
        shutil.copy(
            src=self.charging_station_file,
            dst=self.scenario_path / self.config.charging_stations_path,
        )

        self.scenario_path.joinpath("out").mkdir()

    def generate_scenario(self) -> None:
        self.logger.info("Generating trips")
        self.build_scenario_directory()
        periods: list[float] = self.compute_periods()
        trip_command: str = self.build_random_trip_command(period=periods)
        self.logger.info(f"trip command: {trip_command}")
        self.generate_random_trips(command=trip_command)

        self.logger.info("Generating routes")
        duarouter_command: str = self.build_duarouter_command()
        self.logger.info(f"duarouter command: {duarouter_command}")
        self.convert_trips_to_routes(command=duarouter_command)


def get_scenario_generator_service(
    scenario_path: Path,
    charging_station_file: Path,
    config: generator_config.ScenarioConfig,
    net_file: Path,
    total_vehicle_volume: int,
    logger: Logger,
) -> Service:
    return ScenarioGeneratorService(
        charging_station_file=charging_station_file,
        scenario_path=scenario_path,
        config=config,
        net_file=net_file,
        total_vehicle_volume=total_vehicle_volume,
        logger=logger,
    )
