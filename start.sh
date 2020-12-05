#!/bin/bash

date

sudo service grafana-server start
sudo service mongodb stop
sudo sysctl -w vm.max_map_count=262144
./services start
