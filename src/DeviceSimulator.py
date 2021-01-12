#!/usr/bin/env python3

from time import sleep
from datetime import datetime
import pytz 


import Classes.Entities as Entities
import Classes.DB_Entities as DB_Entities

timezone = pytz.timezone('Europe/London')

fiware = "http://orion:1026"
protocol = "PDI-IoTA-UltraLight"
apikey = "hfe9iuh83qw9hr8ew9her9"
ref = "/iot/d"

def wait4SensorEvents():
	while (not DB_Entities.tabelExist('sensor_events')):
		sleep(1)

def main():

	service = Entities.Service(fiware,apikey,"Devices",ref)
	print(service)
	service.provision()

	lastID = 0

	while True:
		sleep(0.4)
		#read data from MES-DB (sensor events)
		sensor_ev_list = DB_Entities.readNewSensorEvents(lastID,120)

		if len(sensor_ev_list) > 0:
			lastID = list(sensor_ev_list.keys())[-1]

		for sensor_ev in sensor_ev_list.values():
			#register if the sensor doesn't exist in the broker
			if(not(sensor_ev.exists())):
				sensor_ev.provision()
			
			nextTimestamp = sensor_ev.getTimeStamp()
			shiftTime = float(nextTimestamp - datetime.now(timezone).timestamp())

			if(shiftTime>0):
				sleep(shiftTime)

			#Wait until proper TS ...
			sensor_ev.sendData()

if __name__ == "__main__":
		main()
