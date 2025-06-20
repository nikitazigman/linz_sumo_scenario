#!/bin/sh

docker buildx build -t h2mob .
docker run --rm -it --entrypoint bash --name sumo -v ./scenarios:/opt/app/scenarios -v ./config:/opt/app/config h2mob