#!/usr/bin/env python3

import sys
from datetime import datetime 
import pytz 
#import pause
from time import sleep

import Classes.DB_Entities as DB_Entities

timezone = pytz.timezone('Europe/London')

def event_simulation(eventDict):

	previousTimestemp=0
	shiftTime=0
	diff=0
	failed=0
	sucessed=0

	start_event_simulation = datetime.now(timezone)

	for ts,ev in eventDict.items():
		nextTimestamp = datetime.strptime(ev.getTimestamp(), '%Y/%m/%d %H:%M:%S').timestamp()

		print(ev.getTimestamp(),datetime.now(timezone))

		shiftTime = float(nextTimestamp - datetime.now(timezone).timestamp())

		print(shiftTime)

		if(shiftTime>0):
			sleep(shiftTime)
		#pause.until(ts)

		#ev.setTimestamps(datetime.datetime.now())
		#print(datetime.datetime.now())
		if not(ev.insert()):
			failed = failed+1
		else:
			sucessed = sucessed+1
			
		nextTimestamp=0

	end_event_simulation = datetime.now()
	operations_failed2insert = failed
	operations_sucessed2insert = sucessed

	return start_event_simulation,end_event_simulation,operations_failed2insert,operations_sucessed2insert

def main(argv):
	WC_csv = 'WorkCenter.csv'
	Part_csv = 'Part.csv'
	Order_csv = 'order_change_status_5'
	Operation_csv = 'operations_change_status_alt_5'
	time_scale = 2000 # 2000 times faster

	if len(argv) == 5:
		WC_csv = argv[0]
		Part_csv = argv[1]
		Order_csv = argv[2]
		Operation_csv = argv[3]
		time_scale = float(argv[4])
	else:
		print('Event_simulation.py WorkCenter.csv Part.csv Order.csv Operation.csv time_scale')
		sys.exit()

	#Read CSV file and prepare DB ...
	print("Start...")
	DB_Entities.setStaticEntities(WC_csv,Part_csv)

	#Orders and operation events
	eventDict,opEventList = DB_Entities.readCSV(Order_csv,Operation_csv)

	keys_list = list(eventDict.keys())
	actual_start_day = keys_list[0]
	actual_last_day = keys_list[-1]
	actual_time = actual_last_day-actual_start_day
	virtual_time = actual_time/time_scale
	virtual_start_day = datetime.now()
	virtual_last_day = virtual_start_day + virtual_time

	print("\nActual interval time: " + str(actual_time))
	print("Actual first event day: " + str(actual_start_day))
	print("Last event day: " + str(actual_last_day))
	print("The simulation will run " + str(time_scale) + " times faster")
	print("\nVirtual interval time: " + str(virtual_time))
	print("Virtual first event day: " + str(virtual_start_day))
	print("Virtual Last event day: " + str(virtual_last_day))
	expected_end = virtual_start_day+virtual_time
	print("Expected end of the simulation: " + str(expected_end) + "\n")
	
	for key,ev in eventDict.items():
		ev.updateDates(actual_start_day,virtual_start_day,time_scale)

	#Event simulation
	st_ev_sim,end_ev_sim,op_failed2insert,op_sucessed2insert = event_simulation(eventDict)

	print("\nEvent simulation start: " + str(st_ev_sim))
	print("End event simulation: " + str(end_ev_sim))
	print("Time interval: " + str(end_ev_sim - st_ev_sim))
	print("End time vs Expected end time: " + str(end_ev_sim - expected_end))
	print("Operations Failed: " + str(op_failed2insert))
	print("Operation Succeeded: " + str(op_sucessed2insert))

	DB_Entities.conn.close()

if __name__ == "__main__":
		main(sys.argv[1:])
