from src.services.vehicle import IVehicleService

import traci


class RunTimeStepListener(traci.StepListener):
    def __init__(self, vehicle_service: IVehicleService) -> None:
        self.vehicle_service = vehicle_service
        self.rerouted_vehicles = set[str]()

    def handle_vehicles_with_low_fuel(self, vehicles: set[str]) -> None:
        new_vehicles = vehicles.difference(self.rerouted_vehicles)
        if not new_vehicles:
            return

        rerouted_vehicles = self.vehicle_service.fuel_level_handler(
            new_vehicles
        )
        self.rerouted_vehicles.update(rerouted_vehicles)

    def step(self, t: int) -> bool:
        h_vehicles = self.vehicle_service.get_h_vehicles_in_simulation()
        if not h_vehicles:
            return True

        self.handle_vehicles_with_low_fuel(h_vehicles)

        return True
