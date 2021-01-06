
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


#Simulation Variables
export DB_NAME="Fake_MES_DB"
export DB_USER="client"
export DB_PASSWORD="123456"
export DB_IP_ADDRESS="localhost"
#export DB_IP_ADDRESS="192.168.1.2"
export DB_PORT_ADDRESS="5432"
export FIWARE_IP_ADDRESS="localhost"
#export FIWARE_IP_ADDRESS="192.168.1.2"
export FIWARE_PORT_ADDRESS=${ORION_PORT}
export DELAYANALYSIS_IP_ADDRESS="192.168.2.199" 
export DELAYANALYSIS_PORT_ADDRESS="40001"

time_scale="700"
export TIME_SCALE=$time_scale

order_csv="./csv_files/Order_2_weeks.csv"
operation_csv="./csv_files/Operation_2_weeks.csv"

echo "Time scale set to $TIME_SCALE:1"

#Docker execution
cd ./docker
./start.sh
cd -

#Production Line Simulation
./src/MES-Generator.py ${order_csv} ${operation_csv} ${time_scale} &

#DelayAnalysis
./src/delayAnalysis.py > delayAnalysis_log &

#DataProvider
./src/proxy.py > proxy_log &

#Device Simulation
./src/device_simulator.py > device_simulator_log &

wait
