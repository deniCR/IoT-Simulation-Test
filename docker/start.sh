#!/bin/bash

date

export ORION_PORT="1026"
export QUANTUMLEAP_PORT="1"
export IOTA_NORTH_PORT="4041"
export IOTA_SOUTH_PORT="7896"
export MONGO_DB_PORT="27017"
export CRATE_DB_ADMIN="4200"
export CRATE_DB_TP="4300"
export CRATE_DB="54322"

sudo service grafana-server start
sudo service mongodb stop
sudo sysctl -w vm.max_map_count=262144

./services start
