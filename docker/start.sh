#!/bin/bash

# Start the Grafana server if needed
#sudo service grafana-server start
# Stop services that can interfere with the simulation (or change the ports used)
#sudo service mongodb stop
#sudo service postgresql stop

# if the system doesn't provide enough memory map areas
#sudo sysctl -w vm.max_map_count=262144

./services start
