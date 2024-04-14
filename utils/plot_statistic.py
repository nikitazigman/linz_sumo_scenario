from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree

import matplotlib.pyplot as plt
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
SUMO_DIR = BASE_DIR / "scenarios/linz_scenario/out/summary.out.xml"

profile: dict = defaultdict(list)


def parse_statistics_file() -> None:
    tree = ElementTree.parse(SUMO_DIR)
    root = tree.getroot()
    for statistic in root.findall("step"):
        profile["time"].append(float(statistic.attrib["time"]))
        profile["runnings"].append(int(statistic.attrib["running"]))
        profile["inserted"].append(int(statistic.attrib["inserted"]))

    data_frame = pd.DataFrame(profile)
    data_frame.plot(x="time", y="runnings")
    plt.savefig("profile.png")
    plt.show()


if __name__ == "__main__":
    parse_statistics_file()
