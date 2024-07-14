import subprocess
import rich
from abc import ABC, abstractmethod
from pathlib import Path

from scenario_generator.settings import generator_config


class Service(ABC):
    @abstractmethod
    def __init__(
        self,
        config: generator_config.ScenarioConfig,
        hydrogen_vehicles: float,
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
        hydrogen_vehicles: float,
        scenario: Path,
        total_vehicle_volume: int,
    ) -> None:
        self.net_file = scenario / config.net_file_path
        self.route_file = scenario / config.route_file_path
        self.trip_file = scenario / config.trip_file_path
        self.vehicle_type_file = config.vehicle_type_config_path
        self.hydrogen_vehicles = hydrogen_vehicles
        self.total_vehicle = total_vehicle_volume

        self.trafic_profile = config.volume_profile
        self.start_time_sec = 0
        self.stop_time_sec = 24 * 3600
        self.min_distance_m = config.min_trip_distance_m
        self.max_distance_m = config.max_trip_distance_m
        self.prefix = config.prefix
        self.vehicle_type = config.vehicle_type

    def generate_scenario(self) -> None:
        ...

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

        rich.print(f"Successfully generated random traffic: \n{response[0].decode('utf-8')}")
        return None


def generate_random_traffic_for_24h(total_volume: int, scenario: str) -> None:
    traffic_volume_profile: dict[int, float] = {
        0: 0.01 * total_volume,
        1: 0.01 * total_volume,
        2: 0.01 * total_volume,
        3: 0.01 * total_volume,
        4: 0.01 * total_volume,
        5: 0.01 * total_volume,
        6: 0.02 * total_volume,
        7: 0.04 * total_volume,
        8: 0.06 * total_volume,
        9: 0.06 * total_volume,
        10: 0.05 * total_volume,
        11: 0.05 * total_volume,
        12: 0.05 * total_volume,
        13: 0.05 * total_volume,
        14: 0.06 * total_volume,
        15: 0.06 * total_volume,
        16: 0.06 * total_volume,
        17: 0.06 * total_volume,
        18: 0.06 * total_volume,
        19: 0.07 * total_volume,
        20: 0.07 * total_volume,
        21: 0.05 * total_volume,
        22: 0.04 * total_volume,
        23: 0.03 * total_volume,
        24: 0.02 * total_volume,
    }

    root_dir = Path(__file__).parent.parent
    vehicle_type_path = root_dir / "configs/vehicles_types.add.xml"

    scenario_path = root_dir / scenario
    net_file_path = scenario_path / "net.net.xml"
    route_file_path = scenario_path / "routes.rou.xml"
    trip_file_path = scenario_path / "trips.trips.xml"

    periods: list[float] = []

    for i in range(0, 24):
        t0, t1 = i * 3600, (i + 1) * 3600
        period = (t1 - t0) / traffic_volume_profile[i]
        rounded_period = round(period, 2)
        periods.append(rounded_period)

    generate_random_traffic(
        net_file_path=net_file_path,
        route_file_path=route_file_path,
        trip_file_path=trip_file_path,
        additional_file_path=vehicle_type_path,
        vehicle_type="vehicle_distribution",
        start_time_sec=0,
        end_time_sec=24 * 3600,
        period=periods,
        max_distance_m=30000,
        min_distance_m=1500,
        prefix="vehicle",
    )
