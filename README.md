# How to use
1. Install docker
2. `./docker.sh` on linux/MAC
3. if all is correct you should enter into the container shell
4. `cd h2mob`
5. `poetry shell`
6. `h2mob generate-scenario linz.net.xml charging_stations.add.xml 10000 --scenario-name linz_10000` It will generate scenario with 10_000 vehicles 
7. `h2mob run scenarios/linz_1000 0.1 --hydrogen-stations cs_0,cs_1,cs_2,cs_7  ` it will run the generated scenario with 10% of hydrogen cars in the simulation where cs_0,cs_1,cs_2,cs_7 are hydrogen stations. 
8. The output of the simulation is stored in the `out_...` folder inside the generated scenario 
9. `control+D` to exit the docker container 
**To see more option/description of the cli tool use `--help`**