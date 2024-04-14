from src.services.vehicle import IVehicleService

import traci


class PreLoadedStepListener(traci.StepListener):
    def __init__(self, vehicle_service: IVehicleService) -> None:
        self.vehicle_service = vehicle_service

    def step(self, t: int) -> bool:
        loaded_h_vehicles = self.vehicle_service.get_loaded_h_vehicle_ids()
        if not loaded_h_vehicles:
            return True

        self.vehicle_service.assign_tank_level(loaded_h_vehicles)

        return True
