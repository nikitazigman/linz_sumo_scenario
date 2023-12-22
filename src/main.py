from random import choice

from src.configs.settings import get_settings

import traci

from traci.exceptions import TraCIException


settings = get_settings()


def get_charging_station():
    return choice(["cs_0", "cs_1", "cs_2"])


class StepListener(traci.StepListener):
    def step(self, t) -> bool:
        all_vehicles = traci.simulation.getLoadedIDList()
        h_vehicles = [
            vehicle
            for vehicle in all_vehicles
            if traci.vehicle.getTypeID(vehicle) == "h-vehicle"
        ]
        h_vehicles and print(h_vehicles)
        for vehicle in h_vehicles:
            try:
                traci.vehicle.setColor(vehicle, [0, 0, 255])
                traci.vehicle.setVia(vehicle, "E7")
                traci.vehicle.rerouteTraveltime(vehicle)
                charging_station = get_charging_station()
                traci.vehicle.setChargingStationStop(
                    vehicle, charging_station, 5 * 60, 0
                )
            except TraCIException:
                print(f"Vehicle {vehicle} not route found")

        return True


if __name__ == "__main__":
    traci.start(["sumo-gui", "-c", settings.sumo_scenario])
    step_listener = StepListener()

    traci.addStepListener(step_listener)
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

    traci.close()
