#!/usr/bin/env python3

import requests
import json
from time import sleep
import threading
import random
from io import BytesIO
from termcolor import colored

from http.server import HTTPServer, BaseHTTPRequestHandler

import Classes.Devices as Devices
import Classes.Entities as Entities

actuator_host_ip = "192.168.2.151"
actuator_host_port = 40001

actuators = {}

#class Terminal
class Terminal():
	def __init__(self,worker, rfidSensor, button, led):
		self.worker = worker
		#Sensors
		self.rfidSensor = rfidSensor
		self.button = button
		self.led = led

	def provision(self):
		self.worker.provision()
		#Sensors provision
		self.rfidSensor.provision()
		self.button.provision()
		self.led.provision()
		self.led.sendData()

	#Function of initialization
	def init_script(self):
		self.rfidSensor.sendData(self.worker.getRFIDCode())

		#Wait until led changes color - Off, Red or Green
		while self.led.color=='None':
			sleep(1)

		#The command has been received 
		self.led.execCommand("Off")

	#Command to indicate the end of the current task
	def nextTask(self):
		self.button.nextTask()
		#Wait until led changes color - Off, Red or Green
		while self.led.color=='None':
			sleep(0.25)
			pass

		#The command has been received 
		self.led.execCommand("Off")

	def toString(self):
		return self.worker.toString()

def execCommand(json_mensage):
	msg = json_mensage.split("@")
	device = actuators[msg[0]]
	commands = msg[1].split("|")
	for c in commands:
		device.execCommand(c)
		pass

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()		

    def do_POST(self):
        print(colored("\nNotification received!!!","green"), flush=True)

        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)

        self.send_response(200)
        self.end_headers()

        response = BytesIO()
        response.write(b'This is POST request. ')
        response.write(b'Received: ')
        response.write(body)
        self.wfile.write(response.getvalue())

        json_text = body.decode('utf8')

        if self.path > '/iot/':
        	path = self.path.split("/")
        	if path[2] > '':
        		execCommand(json_text)
        		#threading.Thread(target=execCommand, args=(json_text,))
        	pass

def serverStart():
	httpd = HTTPServer((actuator_host_ip, actuator_host_port), SimpleHTTPRequestHandler)
	httpd.serve_forever()

def simulateDevice(device, samples, stop):
	sleeptime = float(1.0/samples)
	print(sleeptime)

	i=0
	while True:
		device.sendData()
		if stop():
			break
		i+=1
		sleep(sleeptime)
		pass

def simulateTerminal(terminal, sample, stop):
	sleeptime = float(60.0/sample)

	terminal.provision()
	terminal.initScript()

	i=0
	while True:
		terminal.nextTask()
		if stop():
			break
		i+=1
		print(terminal.toString() + " " + str(i))
		sleep_for = random.random()*sleeptime
		if sleep_for < 1:
			sleep_for = 1
		print("Sleep for :" + str(sleep_for))
		sleep(sleep_for)
		pass

def readConfFile(file):
	run_time = 0
	apikey = ""
	devices = []
	terminals = []
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
				service = Entities.Service(x[1],x[2],x[3],x[4])
				apikey = x[2]

			if key == 'device':
				type = x[1]
				if type == 't':
					devices.append(Devices.TempSensor(t,x[2],apikey,x[3]))
					t+=1
				if type == 'h':
					devices.append(Devices.HumSensor(h,x[2],apikey,x[3]))
					h+=1
				if type == 'l':
					devices.append(Devices.LightSensor(l,x[2],apikey,x[3]))
					l+=1
				if type == 'c':
					devices.append(Devices.CO2Sensor(t,x[2],apikey,x[3]))
					t+=1
				sample.append(int(x[5]))

			#if key == 'actuator':
			#	type = x[1]
			#	if type == 'led':
			#		led_device = Devices.Led(led,x[2],apikey,x[3])
			#		#devices.append(led_device)
			#		actuators["led"+str(led)]=(led_device)
			#		led+=1
			#	sample.append(int(x[5]))

			if key == 'worker':
				rfid_aux = Devices.RFIDSensor(r,x[1],apikey,x[4])
				r+=1
				button_aux = Devices.Button(b,x[1],apikey,x[4])
				b+=1
				led_aux = Devices.Led(led,x[1],apikey,x[4])
				actuators["led"+str(led)]=(led_aux)
				led+=1
				worker_aux = Entities.Worker(w,x[2],x[3])
				terminals.append(Terminal(worker_aux,rfid_aux,button_aux,led_aux))
				w+=1
				sample.append(int(x[5]))

			#print(line + "\n" + str(w) + "\n")
			line = file_object.readline()


	return run_time,service,devices,terminals,sample

def main():
	run_time=0
	#read from confg file ...
	run_time,service,devices,terminals,sample=readConfFile('DummyDevices.conf')

	service.provision()
	
	stop_threads = False
	threads = []
	
	i=0
	for d in devices:
		d.provision()
		threads.append(threading.Thread(target=simulateDevice,args=(d,sample[i],lambda : stop_threads,)))
		i+=1

	for t in terminals:
		threads.append(threading.Thread(target=simulateTerminal,args=(t,sample[i],lambda : stop_threads,)))
		i+=1

	for t in threads:
		t.start()

	serverStart()

	#The threads will run until the time is completed...
	sleep(run_time)
	stop_threads=True

	for t in threads:
		t.join()

if __name__ == "__main__":
		main()


