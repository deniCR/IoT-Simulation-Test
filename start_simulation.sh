#!/bin/bash

#Kill all subprocess when CTRL+C is pressed
trap "kill -15 0" INT

#Variables
export DB_NAME="Fake_MES_DB"
export DB_USER="client"
export DB_PASSWORD="123456"
export DB_IP_ADDRESS="192.168.2.199"
export DB_PORT_ADDRESS="5432"
export FIWARE_IP_ADDRESS="192.168.2.199"
export FIWARE_PORT_ADDRESS="1026"
export DELAYANALYSIS_IP_ADDRESS="192.168.2.151"
export DELAYANALYSIS_PORT_ADDRESS="40001"
#Agent broker ...
#Agent device  ...


workcenter_csv="./src/csv_file/Workcenter.csv"
partnumber_csv="./src/csv_file/Part.csv"
order_csv="./src/csv_file/Order.csv"
operation_csv="./src/csv_file/operations_change_status_alt_7"
time_scale="3000"

#Execution
#./start_fiware

./src/MES-Generator.py ${workcenter_csv} ${partnumber_csv} ${order_csv} ${operation_csv} ${time_scale} &

#Wait for FIWARE to start

./src/delayAnalysis.py > delayAnalysis_log &

./src/proxy.py > proxy_log &

#./src/device_simulator.py > device_simulator_log &

wait
