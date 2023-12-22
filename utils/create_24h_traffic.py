import subprocess

from pathlib import Path


def generate_random_traffic(
    net_file_path: Path,
    route_file_path: Path,
    trip_file_path: Path,
    additional_file_path: Path,
    vehicle_type: str,
    start_time_sec: int,
    end_time_sec: int,
    period: list[float],
    max_distance_m: float,
    min_distance_m: float,
    prefix: str,
) -> None:
    period_str = ",".join([str(p) for p in period])
    command = (
        "python /opt/homebrew/share/sumo/tools/randomTrips.py "
        f"--net-file {net_file_path} "
        f"-o {trip_file_path} "
        f"--additional-files {additional_file_path} "
        f"""--trip-attributes="type='{vehicle_type}'" """
        f"--begin {start_time_sec} "
        f"--end {end_time_sec} "
        f"-p {period_str} "
        f"--max-distance {max_distance_m} "
        f"--min-distance {min_distance_m} "
        f"--prefix {prefix} "
        f"--route-file {route_file_path} "
        f"--random "
        # f"--verbose"
    )
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
        print(
            f"Successfully generated random traffic: \n{response[0].decode('utf-8')}"
        )

    return None


def generate_random_traffic_for_24h(total_volume: int) -> None:
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

    scenario_path = Path(__file__).parent.parent / "test_scenario"
    net_file_path = scenario_path / "osm.net.xml.gz"
    vehicle_type_path = scenario_path / "vehicles_types.add.xml"

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
        max_distance_m=10000,
        min_distance_m=1500,
        prefix=f"route_{i}_",
    )


if __name__ == "__main__":
    generate_random_traffic_for_24h(total_volume=10_000)
