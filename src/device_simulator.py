#!/usr/bin/env python3

from time import sleep

import Classes.Entities as Entities
import Classes.DB_Entities as DB_Entities

fiware = "http://orion:1026"
protocol = "PDI-IoTA-UltraLight"
apikey = "hfe9iuh83qw9hr8ew9her9"
ref = "/iot/d"

def main():

	service = Entities.Service(fiware,apikey,"Devices",ref)
	print(service)
	service.provision()

	lastID = 0

	while True:
		#read data from MES-DB (sensor events)
		sensor_ev_list = DB_Entities.readNewSensorEvents(lastID)

		if len(sensor_ev_list) > 0:
			lastID = list(sensor_ev_list.keys())[-1]

		for sensor_ev in sensor_ev_list.values():
			sleep(0.1)
			#register if the sensor doesn't exist in the broker
			if(not(sensor_ev.exists())):
				sensor_ev.provision()
			#Wait until proper TS ...
			sensor_ev.sendData()

if __name__ == "__main__":
		main()