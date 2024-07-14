from typing import Annotated

import typer

from rich.traceback import install


install(show_locals=True)
app = typer.Typer()


@app.command()
def generate_scenario(
    hydrogen_vehicles: Annotated[float, typer.Argument()],
    scenario_path: Annotated[str, typer.Argument()],
    total_vehicles: Annotated[str, typer.Argument()],
):
    raise ValueError("test exception")


if __name__ == "__main__":
    app()
