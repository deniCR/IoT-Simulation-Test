#!/usr/bin/env python3

from http.server import HTTPServer, BaseHTTPRequestHandler
from time import sleep
import json
import os

import Classes.HTTPCommands as HTTPCommands
import Classes.Entities as Entities

url_sub = "http://" + os.environ['FIWARE_IP_ADDRESS'] + ":" + os.environ['FIWARE_PORT_ADDRESS'] + "/v2/subscriptions/?options=skipInitialNotification"

Order_subscription = {
	"description": "Notify DelayAnalysis of all Order",
	"subject": { 
		"entities": [{"idPattern": ".*", "type": "Order"}],
		"condition": {"attrs": ["statusChangeTS","scheduledDelay","progressDelay"],
						"expression": {"q": "scheduledDelay=='-';progressDelay=='-'"}}
	},
	"notification": {
		"http": {
			"url": "http://" + os.environ['DELAYANALYSIS_IP_ADDRESS'] + ":" + os.environ['DELAYANALYSIS_PORT_ADDRESS'] + "/notify/Order",
			"accept": "application/json"
		},
		"attrs": [
			"scheduledStart","scheduledEnd","actualStart","orderNewStatus","statusChangesTS",
			"actualEnd","currentHours","plannedHours","totalHours","actualProgress","scheduledDelay","progressDelay"
			],
		"attrsFormat": "keyValues"
	},
}

Progress_subscription = {
	"description": "Notify DelayAnalysis of all progressSensor measurements",
	"subject": { 
		"entities": [{"idPattern": ".*", "type": "ProgressSensor"}],
		"condition": {"attrs": ["progress"]}
	},
	"notification": {
		"http": {
			"url": "http://" + os.environ['DELAYANALYSIS_IP_ADDRESS'] + ":" + os.environ['DELAYANALYSIS_PORT_ADDRESS'] + "/notify/Progress",
			"accept": "application/json"
		},
		"attrs": [
			"progress","timeStamp","operationNumber","orderNumber","workcenter_id"
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

			print(r)

			ord = Entities.Order(r["id"][18:])
			ord.loadJsonEntity(r)

			ord.processDelay()

			if ord.getAttrValue("orderNewStatus") in ("COMPLETE","CANCELLED"):
				ord.deleteAll()

def processProgress(body):
	notification = json.loads(body)

	if "data" in notification:
		for r in notification["data"]:
			if "workcenter_id" in r:
				wc_id = r["workcenter_id"]
				ev_ts = r["timeStamp"]
				op_number = r["operationNumber"]
				order_number = r["orderNumber"]

				#print(r)

				op = Entities.Operation()
				_query=("q=workCenter_id==\'" + str(wc_id) + "\';orderNumber==\'" + str(order_number) + "\';operationNumber==\'" + str(op_number) +  "\';statusChangeTS<=" + str(ev_ts) + ";operationNewStatus=='RUN'&type=Operation&options=keyValues,count&limit=5&orderBy=!statusChangeTS")
				
				#print(_query)

				if op.get(query=_query):

					actualProgress = int(r["progress"])
					prevProgress = op.getAttrValue("actualProgress")
					if prevProgress == None:
						prevProgress = -1

					op_q = op.getAttrValue("operationNumber")
					if op_number != op_q:
						print("Operation expected: " + str(op_number) + " operation query: " + str(op.getAttrValue("operationNumber")))
					
					#Update the process state ...
					if actualProgress > prevProgress:
						op.processDelay(actualProgress,ev_ts)

						#Update process state of the Order ...
						ord_id = op.getOrderID()
						ord_id = "urn:ngsi-ld:Order:" + str(ord_id)

						if ord_id!=None:
							ord = Entities.Order()

							if ord.getEntity(entity_id=ord_id):
								ord.processOperationProgress(op,actualProgress,ev_ts)


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

	def do_GET(self):
		self.send_response(200)
		self.end_headers()

	def do_POST(self):

		content_length = int(self.headers['Content-Length'])
		body = self.rfile.read(content_length)
		self.send_response(200)
		self.end_headers()

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
