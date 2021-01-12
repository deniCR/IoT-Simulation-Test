
#!/bin/bash

#Kill all subprocess when CTRL+C is pressed
trap "kill -15 0" INT

date

#Docker-composer variables $$ overwrites the ./docker/.env variables
# Orion
export ORION_PORT="1026"
export ORION_VERSION="2.5.2"
# MongoDB
export MONGO_DB_PORT="27017"
export MONGO_DB_VERSION="4.4.3"
# IoT Agent Ultralight
export ULTRALIGHT_VERSION="1.13.0"
export IOTA_NORTH_PORT="4041"
export IOTA_SOUTH_PORT="7896"
# Tutorial
export TUTORIAL_APP_PORT="3000"
export TUTORIAL_DUMMY_DEVICE_PORT="3001"
# QuantumLeap
export QUANTUMLEAP_VERSION="0.7.5"
export QUANTUMLEAP_PORT="8668"
# Crate-db
export CRATE_DB_VERSION="3.2"
export CRATE_DB_ADMIN="4200"
export CRATE_DB_TP="4300"
export CRATE_DB="54322"
#Postgresql DB
export POSTGRES_VERSION="12.0"
export POSTGRES_PORT="49100"
export POSTGRES_USER="client"
export POSTGRES_PASSWORD="123456"
export POSTGRES_DB="Fake_MES_DB"
export POSTGRES_IP="localhost"
#export DB_IP_ADDRESS="192.168.1.2"
export DB_PORT_ADDRESS=${POSTGRES_PORT}
#Grafana
export GRAFANA_PORT="3003"
export GRAFANA_VERSION="7.3.6"

#Simulation Variables
export FIWARE_IP_ADDRESS="localhost"
#export FIWARE_IP_ADDRESS="192.168.1.2"
export FIWARE_PORT_ADDRESS=${ORION_PORT}
export DELAYANALYSIS_IP_ADDRESS="192.168.2.199" 
export DELAYANALYSIS_PORT_ADDRESS="40001"

time_scale="1500"
export TIME_SCALE=$time_scale

order_csv="./csv_files/Order_2_weeks.csv"
operation_csv="./csv_files/Operation_2_weeks.csv"

echo "Time scale set to $TIME_SCALE:1"

#Docker execution
cd ./docker
./start.sh
cd -

sleep 5

#Production Line Simulation
./src/ProductionLineSimulator.py ${order_csv} ${operation_csv} ${time_scale} &

#Time to create the database and the tables
sleep 3

#DelayAnalysis
./src/DelayAnalysis.py > delayAnalysis_log &

#DataProvider
./src/DataProvider.py > proxy_log &

#Device Simulation
./src/DeviceSimulator.py > device_simulator_log &

wait
