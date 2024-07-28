from pathlib import Path

from pydantic_settings import BaseSettings


ROOT_UTILS_PATH = Path(__file__).resolve().parent.parent.parent


class GeneralConfig(BaseSettings):
    route_file_path: str = "routes.rou.xml"
    sumocfg_file_path: str = "osm.sumocfg"
    trip_file_path: str = "trips.trips.xml"
    vehicle_type_path: str = "vehicle_type.xml"
    net_path: str = "osm.net.xml"
    charging_stations_path: str = "charging.add.xml"
