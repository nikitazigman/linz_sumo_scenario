# How to use
0. USE `Eclipse SUMO sumo Version 1.20.0`
1. Install poetry 
3. if all is correct you should enter into the container shell
4. `cd h2mob`
5. `poetry shell`
6. `cd ..`
7. `h2mob generate-scenario ./config/linz.net.xml ./config/charging_stations.add.xml 1000 ./scenarios/linz_1000` It will generate scenario with 10_000 vehicles 
8. `h2mob run scenarios/linz_1000 0.1 --hydrogen-stations cs_0,cs_1,cs_2,cs_7` it will run the generated scenario with 10% of hydrogen cars in the simulation where cs_0,cs_1,cs_2,cs_7 are hydrogen stations. 
9. The output of the simulation is stored in the `out_...` folder inside the generated scenario 
```bash
├── battery.out.xml
├── chargingstations.out.xml
├── fcd.out.xml
├── scenario_config.json
├── statistics.out.xml
└── summary.out.xml
```
10. `control+D` to exit the docker container 
**To see more option/description of the cli tool use `--help`**