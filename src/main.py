import time

from src.configs.scenario_config import get_scenario_config
from src.configs.settings import get_settings
from src.services.vehicle import get_vehicle_service
from src.step_listeners.loaded_vehicles import PreLoadedStepListener
from src.step_listeners.simulated_vehicles import RunTimeStepListener
from src.storages.simulation import get_simulation_storage
from src.utils.scenario_parser import get_sumo_scenario_parser

import traci

from loguru import logger


def system_init() -> None:
    logger.info("Starting the simulation")

    settings = get_settings()

    scenario_parser = get_sumo_scenario_parser(settings.sumo_scenario_path)
    scenario_config = get_scenario_config(scenario_parser)

    traci.start(["sumo-gui", "-c", settings.sumo_scenario_path])

    simulation_storage = get_simulation_storage(traci, scenario_config)

    vehicle_service = get_vehicle_service(simulation_storage)

    runtime_listener = RunTimeStepListener(vehicle_service=vehicle_service)
    loaded_listener = PreLoadedStepListener(vehicle_service=vehicle_service)

    traci.addStepListener(runtime_listener)
    traci.addStepListener(loaded_listener)


def run_simulation_loop() -> None:
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()


def system_shutdown() -> None:
    logger.info("Simulation ended")
    traci.close()


def main():
    system_init()
    start = time.time()
    try:
        run_simulation_loop()
    except KeyboardInterrupt:
        logger.warning("Simulation interrupted by user.")
    except traci.FatalTraCIError as e:
        logger.error(f"Simulation ended with error: {e}")
    finally:
        end = time.time()
        logger.info(f"Simulation took {end - start} seconds.")
        system_shutdown()


if __name__ == "__main__":
    main()
