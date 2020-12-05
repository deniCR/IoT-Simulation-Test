#!/bin/bash

date

#Depending on the configuration of the docker, the use of authorizations (sudo) may be unnecessary
sudo service grafana-server start
sudo service mongodb stop
sudo sysctl -w vm.max_map_count=262144

./services start
