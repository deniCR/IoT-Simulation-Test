#!/usr/bin/env python3

from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
from time import sleep
import requests
import json
import datetime

import Classes.HTTPCommands as HTTPCommands
import Classes.Entities as Entities

url_sub = "http://192.168.2.108:1026/v2/subscriptions/?options=skipInitialNotification"

Order_subscription = {
	"description": "Notify DelayAnalysis of all Order",
	"subject": { 
		"entities": [{"idPattern": ".*", "type": "Order"}],
		"condition": {"attrs": ["statusChangeTS"]}
	},
	"notification": {
		"http": {
			"url": "http://192.168.2.151:40000/notify/Order",
			"accept": "application/json"
		},
		"attrs": [
			"scheduledStart","scheduledEnd","actualStart",
			"actualEnd","planedHours","actualHours","numberOfEndedOperations","numberOperations"
			],
		"attrsFormat": "keyValues"
	},
}

def wait4Service():
	url_services = "http://192.168.2.108:4041/iot/services/?service=openiot"
	payload_service = {}
	count = 0
	while count==0:
		response = HTTPCommands.sendRequest("GET",url_services,HTTPCommands.iot_headers,json.dumps(payload_service))
		response_json = json.loads(response)
		count = int(response_json["count"])
		if count==0:
			sleep(1)
			pass

def processOrders(body):
	notification = json.loads(body)

	if "data" in notification:
		for r in notification["data"]:
			ord = Entities.Order(r["id"][18:])
			ord.loadJsonEntity(r)

			ord.processScheduleDelay()
			ord.processProgressDelay()

			print(ord.toString())

			ord.update()
#			if r["orderStaus"]=="SCHEDULED":
#				#Update precess status => 0%
#
#			else:
#				if notification["data"][0]["orderStaus"]=="RUNNING":
#					#Calculate and update process status ...
#					
#					ord = Order(r)
#					ord.updateProcessStatus()
#				else:
#					if notification["data"][0]["orderStaus"]=="COMPLETED":
#
#						#--- DELETE from orion ...


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

	def do_GET(self):
		self.send_response(200)
		self.end_headers()

	def do_POST(self):

		content_length = int(self.headers['Content-Length'])
		body = self.rfile.read(content_length)

		self.send_response(200)
		self.end_headers()

		json_text = body.decode('utf8')

		if self.path=='/notify/Order':
			#print(body)
			processOrders(body)
			pass

def main():

	#wait4Service()
	print("The Service has been created!")

	#Subscriptions ...
	HTTPCommands.sendRequest("POST",url_sub,HTTPCommands.iot_headers,json.dumps(Order_subscription))

	print("Start server ...", flush=True)
	httpd = HTTPServer(("", 40000), SimpleHTTPRequestHandler)
	httpd.serve_forever()

if __name__ == "__main__":
		main()
