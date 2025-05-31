from pathlib import Path
from typing import Annotated

from h2mob.services.generate_scenario import get_scenario_generator_service
from h2mob.services.simulation import get_simulation_service
from h2mob.settings.generator_config import get_scenario_conf
from h2mob.settings.simulation import SimulationConfig, get_simulation_config

import typer

from loguru import logger
from rich.traceback import install


install(show_locals=True)
app = typer.Typer()


@app.command()
def generate_scenario(
    net_file: Annotated[Path, typer.Argument()],
    charging_station_file: Annotated[Path, typer.Argument()],
    total_vehicles: Annotated[int, typer.Argument()],
    scenario_path: Annotated[Path, typer.Argument()],
) -> None:
    config = get_scenario_conf()
    service = get_scenario_generator_service(
        config=config,
        net_file=net_file,
        charging_station_file=charging_station_file,
        total_vehicle_volume=total_vehicles,
        scenario_path=scenario_path,
        logger=logger,
    )
    service.generate_scenario()


@app.command()
def run(
    scenario_path: Annotated[Path, typer.Argument()],
    percent_of_hydrogen_cars: Annotated[float, typer.Argument()],
    hydrogen_stations: Annotated[str | None, typer.Option()] = None,  # noqa
) -> None:
    hstation: set[str] = (
        set()
        if hydrogen_stations is None
        else {station.strip() for station in hydrogen_stations.split(",")}
    )
    logger.info(f"hydrogen stations {hstation}")
    config: SimulationConfig = get_simulation_config()
    service: Service = get_simulation_service(
        logger=logger,
        percent_of_hydrogen_cars=percent_of_hydrogen_cars,
        hydrogen_stations=hstation,
        simulation_config=config,
        scenario_path=scenario_path,
    )
    service.run()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
