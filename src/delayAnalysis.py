#!/usr/bin/env python3

from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
from time import sleep
import requests
import json
import datetime
import os

import Classes.HTTPCommands as HTTPCommands
import Classes.Entities as Entities

url_sub = "http://" + os.environ['FIWARE_IP_ADDRESS'] + ":" + os.environ['FIWARE_PORT_ADDRESS'] + "/v2/subscriptions/?options=skipInitialNotification"

Order_subscription = {
	"description": "Notify DelayAnalysis of all Order",
	"subject": { 
		"entities": [{"idPattern": ".*", "type": "Order"}],
		"condition": {"attrs": ["statusChangeTS"]}
	},
	"notification": {
		"http": {
			"url": "http://" + os.environ['DELAYANALYSIS_IP_ADDRESS'] + ":" + os.environ['DELAYANALYSIS_PORT_ADDRESS'] + "/notify/Order",
			"accept": "application/json"
		},
		"attrs": [
			"scheduledStart","scheduledEnd","actualStart","orderNewStatus","statusChangesTS",
			"actualEnd","totalActualHours","totalPlanedHours","totalNumberOfEndedOperations","totalNumberOfOperations","scheduledDelay"
			],
		"attrsFormat": "keyValues"
	},
}

Progress_subscription = {
	"description": "Notify DelayAnalysis of all progressSensor measurements",
	"subject": { 
		"entities": [{"idPattern": ".*", "type": "ProgressSensor"}],
		"condition": {"attrs": ["Progress"]}
	},
	"notification": {
		"http": {
			"url": "http://" + os.environ['DELAYANALYSIS_IP_ADDRESS'] + ":" + os.environ['DELAYANALYSIS_PORT_ADDRESS'] + "/notify/Progress",
			"accept": "application/json"
		},
		"attrs": [
			"progress","timeStamp","operationNumber","workcenter_id"
			],
		"attrsFormat": "keyValues"
	},
}

def wait4Service():
	url_services = "http://" + os.environ['FIWARE_IP_ADDRESS'] + ":4041/iot/services/?service=openiot"
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

			ord.processDelay()

			if ord.getAttrValue("orderNewStatus") == "COMPLETE" or ord.getAttrValue("orderNewStatus") == "CANCELLED":
				ord.deleteAll()

def processProgress(body):
	notification = json.loads(body)

	if "data" in notification:
		for r in notification["data"]:
			if "workcenter_id" in r:
				wc_id = r["workcenter_id"]
				ev_ts = r["timeStamp"]
				op_number = r["operationNumber"]

				print(r)

				op = Entities.Operation()
				_query=("q=workCenter_id==\'" + str(wc_id) + "\';operationNewStatus=='RUN';statusChangeTS>='" + str(ev_ts) + "'&type=Operation&options=keyValues&limit=1&orderBy=!statusChangeTS")
				
				if op.get(query=_query):

					newProgress = r["Progress"]
					#Update the process state ...
					print("Operation progress: " + newProgress)
					print("Operation expected: " + op_number + " operation query: " + op.getAttrValue("operationNumber"))
					op.processProgress(newProgress)

					#Update process state of the Order ...
					ord_id = op.getOrderID()

					if ord_id!=None:
						print(ord_id)
						ord = Entities.Order()

						if ord.get(entity_id=ord_id):
							ord.processOperationProcess(op,newProgress)
							print(ord)
					else:
						print("ORDER_ID IS NONE ::::")


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
			processOrders(body)

		elif self.path=='/notify/Progress':
			processProgress(body)

def main():

	#develop wait service ...
	#wait4Service()
	print("The Service has been created!")

	#Subscriptions ...
	HTTPCommands.sendRequest("POST",url_sub,HTTPCommands.iot_headers,json.dumps(Order_subscription))
	HTTPCommands.sendRequest("POST",url_sub,HTTPCommands.iot_headers,json.dumps(Progress_subscription))

	print("Start server ...", flush=True)
	httpd = HTTPServer(('', int(os.environ['DELAYANALYSIS_PORT_ADDRESS'])), SimpleHTTPRequestHandler)
	httpd.serve_forever()

if __name__ == "__main__":
		main()
