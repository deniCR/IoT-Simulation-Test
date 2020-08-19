#!/bin/bash

#Variables
fiware_ip_address="192.168.2.108"
mes_db_ip_address="192.168.2.108"

workcenter_csv="./src/csv_file/Workcenter.csv"
partnumber_csv="./src/csv_file/Part.csv"
order_csv="./src/csv_file/Order.csv"
operation_csv="./src/csv_file/Operation.csv"

time_scale="4000"

#Execution
#./start_fiware

./src/MES-Generator.py ${workcenter_csv} ${partnumber_csv} ${order_csv} ${operation_csv} ${time_scale}
#./src/proxy.py
#./src/delayAnalysis.py