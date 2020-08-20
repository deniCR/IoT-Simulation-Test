#!/bin/bash

#Kill all subprocess when CTRL+C is pressed
trap "kill -TERM 0" INT

#Variables
export DB_IP_ADDRESS="192.168.2.108"
export DB_PORT_ADDRESS="5432"
export FIWARE_IP_ADDRESS="192.168.2.108"
export DELAYANALYSIS_IP_ADDRESS="192.168.2.151"
export DELAYANALYSIS_PORT_ADDRESS="40000"

workcenter_csv="./src/csv_file/Workcenter.csv"
partnumber_csv="./src/csv_file/Part.csv"
order_csv="./src/csv_file/Order.csv"
operation_csv="./src/csv_file/Operation.csv"
time_scale="4000"

#Execution
#./start_fiware

./src/MES-Generator.py ${workcenter_csv} ${partnumber_csv} ${order_csv} ${operation_csv} ${time_scale} &

#Wait for FIWARE to start

./src/delayAnalysis.py > delayAnalysis_log &

./src/proxy.py > proxy_log &

wait