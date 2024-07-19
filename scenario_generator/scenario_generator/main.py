from pathlib import Path
from typing import Annotated

from scenario_generator.services.generate_scenario import get_scenario_generator_service
from scenario_generator.settings.generator_config import get_scenario_conf

import typer

from rich.traceback import install


install(show_locals=True)
app = typer.Typer()


@app.command()
def generate_scenario(
    net_file: Annotated[Path, typer.Argument()],
    total_vehicles: Annotated[int, typer.Argument()],
    scenario_name: str = "scenario",
):
    config = get_scenario_conf()
    service = get_scenario_generator_service(
        config=config,
        net_file=net_file,
        total_vehicle_volume=total_vehicles,
        scenario_name=scenario_name,
    )
    service.generate_scenario()


if __name__ == "__main__":
    app()

