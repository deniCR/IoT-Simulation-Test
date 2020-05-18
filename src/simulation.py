#!/usr/bin/env python3

import requests
import json
from time import sleep
import threading
import random

import Classes.HTTPCommands
import Classes.Devices

def wait4Service():
	url_services = "http://iot-agent:4041/iot/services/?service=openiot"
	payload_service = {}
	count = 0
	while count==0:
		response = get(url_services,headers,json.dumps(payload_service))
		response_json = json.loads(response)
		count = int(response_json["count"])
		if count==0:
			sleep(1)
			pass

def simulate_device(device, samples, stop):
	sleeptime = float(1.0/samples)
	print(sleeptime)

	i=0
	while True:
		device.send_data()
		if stop():
			break
		i+=1
		#print(device.toString() + " " + str(i))
		sleep(sleeptime)
		pass

def simulate_worker(worker, sample, stop):
	sleeptime = float(60.0/sample)

	i=0
	while True:
		worker.next_task()
		if stop():
			break
		i+=1
		print(worker.toString() + " " + str(i))
		sleep(sleeptime)
		pass

def read_conf_file(file):
	run_time = 0
	apikey = ""
	devices = []
	workers = []
	sample = []
	t=0;h=0;l=0;c=0;r=0;b=0;w=0;led=0

	with open(file) as file_object:
		line = file_object.readline()
		while line:
			x = line.split()
			key = x[0]

			if key == 'host':
				host = x[1]

			if key == 'cbroker':
				cbroker = x[1]

			if key == 'run_time':
				run_time = int(x[1])

			if key == 'service':
				service = Classes.Devices.Service(x[1],x[2],x[3],x[4])
				apikey = x[2]

			if key == 'device':
				type = x[1]
				if type == 't':
					devices.append(Classes.Devices.TempSensor(t,x[2],apikey,x[3]))
					t+=1
				if type == 'h':
					devices.append(Classes.Devices.HumSensor(h,x[2],apikey,x[3]))
					h+=1
				if type == 'l':
					devices.append(Classes.Devices.LightSensor(l,x[2],apikey,x[3]))
					l+=1
				if type == 'c':
					devices.append(Classes.Devices.CO2Sensor(t,x[2],apikey,x[3]))
					t+=1
				if type == 'led':
					devices.append(Classes.Devices.Led(led,x[2],apikey,x[3]))
					led+=1
				sample.append(int(x[5]))

			if key == 'worker':
				rfid_aux = Classes.Devices.RFIDSensor(r,x[1],apikey,x[4])
				r+=1
				button_aux = Classes.Devices.Button(b,x[1],apikey,x[4])
				b+=1
				workers.append(Classes.Devices.Worker(w,x[2],x[3],rfid_aux,button_aux))
				w+=1
				sample.append(int(x[5]))

			line = file_object.readline()


	return run_time,service,devices,workers,sample


def main():
	run_time=0
	#read from confg file ...
	run_time,service,devices,workers,sample=read_conf_file('DummyDevices.conf')

	service.provision()
	
	stop_threads = False
	threads = []
	
	i=0
	for d in devices:
		d.provision()
		threads.append(threading.Thread(target=simulate_device,args=(d,sample[i],lambda : stop_threads,)))
		i+=1
		pass

	for w in workers:
		w.provision()
		threads.append(threading.Thread(target=simulate_worker,args=(w,sample[i],lambda : stop_threads,)))
		i+=1
		pass

	for t in threads:
		t.start()
		pass

	#The threads will run until the time is completed...
	sleep(run_time)
	stop_threads=True

	for t in threads:
		t.join()
		pass

if __name__ == "__main__":
		main()


