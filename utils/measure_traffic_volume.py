from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import traci


BASE_DIR = Path(__file__).resolve().parent.parent
SUMO_DIR = BASE_DIR / "test_scenario/osm.sumocfg"

profile: dict[str, list[float]] = {"time": [], "vehicle_count": []}


class StepListener(traci.StepListener):
    def step(self, t) -> bool:
        time = traci.simulation.getTime()
        if time % 3600 == 0:
            vehicle_count = traci.vehicle.getIDCount()
            hour = int(time / 3600)
            print(f"Time: {hour}, vehicle count: {vehicle_count}")
            profile["time"].append(hour)
            profile["vehicle_count"].append(vehicle_count)

        return True


if __name__ == "__main__":
    traci.start(["sumo-gui", "-c", SUMO_DIR])
    step_listener = StepListener()

    traci.addStepListener(step_listener)
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

    traci.close()
    data_frame = pd.DataFrame(profile)
    data_frame.to_csv("profile.csv", index=False)
    data_frame.plot(x="time", y="vehicle_count")
    plt.savefig("profile.png")
    plt.show()
