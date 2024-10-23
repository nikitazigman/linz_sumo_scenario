# How to use
1. Install poetry and Python >= 3.12
2. `cd h2mob` 
3. `poetry shell`
4. `poetry install`
5. `cd ..`
6. `h2mob generate-scenario linz.net.xml charging_stations.add.xml 10000 --scenario-name linz_10000` It will generate scenario with 10_000 vehicles 
7. `h2mob run scenarios/linz_10000 0.1` it will run the generated scenario with 10% of hydrogen cars in the simulation 
8. The output of the simulation is stored in the `out` folder inside the generated scenario 

**To see more option/description of the cli tool use `--help`**