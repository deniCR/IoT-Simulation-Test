#!/usr/bin/env python3

from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
from time import sleep
import requests
import json

import Classes.HTTPCommands as HTTPCommands
import Classes.Entities as Entities

url_sub = "http://192.168.2.108:1026/v2/subscriptions/?options=skipInitialNotification"

rfid_subscription = {
	"description": "Notify Server of all RFID context changes",
	"subject": { 
		"entities": [{"idPattern": ".*", "type": "RFIDSensor"}],
		"watchAttributes": ["Button"],
		"q": "RFID!=\"\""
	},
	"notification": {
		"http": {
			"url": "http://192.168.2.151:40000/notify/RFID",
			"accept": "application/json"
        },
        "attributes": ["RFID","refStation"],
        "attrsFormat": "keyValues"
	},
}

nextTask_subscription = {
	"description": "Notify Server of all NextTask commands",
	"subject": { 
		"entities": [{"idPattern": ".*", "type": "Button"}],
		"watchAttributes": ["Button"],
		"q": "Button!=\"\""
	},
	"notification": {
		"http": {
			"url": "http://192.168.2.151:40000/notify/NextTask",
			"accept": "application/json"
        },
        "attributes": ["Button","refStation"],
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

def processNextTaskNotification(body):
	notification = json.loads(body)

	if "data" in notification:
		for r in notification["data"]:
			if len(notification["data"]) > 0:
				if notification["data"][0]["Button"]=="Stop":

					timeInstant = notification["data"][0]["TimeInstant"]
					station_id = notification["data"][0]["refStation"]

					#Estimation of the process state ...
					update_processState = 10

					#
					# Verify requirements ...
					#
					# If the requirements are not fulfilled send Led "Red"
					#
					# Otherwise ...
					#

					#Update times/process States - Script and Station
					# Get station, get script
					station = Entities.Station()
					station.get(station_id)

					if station != None:
						#Update script State ...
						script = station.getScript()

						if script != None:
							update_payload = {}
							update_payload["stopTime"] = timeInstant
							script.update(update_payload)

							#Update actual task - Script (Check if it is the last task of the script)
							script.nextTask(timeInstant)

							#Send commands - Last Task finished/ Led Green
							led = Entities.Device()
							led.getByStation(station_id)
							led.execCommand("Green")
						else:
							print("The script wasn't retired from the broker: ")
					else:
						print("The station wasn't retired from the broker: " + station_id)


def processRFIDNotification(body):
	notification = json.loads(body)

	if "data" in notification:
		for r in notification["data"]:

			if r["RFID"]!="":
				update_processState = "0%"

			else :
				update_processState = "Stopped"

			timeInstant = r["TimeInstant"]
			#Station reference (get from the subscription)
			station_id = r["refStation"]

			#Get Station info (Script id)
			station = Entities.Station()
			station.get(station_id)


			#Update script State ...
			script = station.getScript()
			script.update({"processState": update_processState})
			script.initScript(timeInstant)

			#Append worker id to the script ...
			worker = Entities.Worker()
			worker.getByRFIDCode(r["RFID"])
			script.update({"refWorker": worker.getID()})

			#Send command 
			led = Entities.Device()
			led.getByStation(station_id)
			led.execCommand("Green")

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

        if self.path=='/notify/RFID':
        	processRFIDNotification(body)
        	pass

        if self.path=='/notify/NextTask':
        	processNextTaskNotification(body)
        	pass

def main():

	wait4Service()
	print("The Service has been created!")

	#Subscriptions ...
	#HTTPCommands.sendRequest("POST",url_sub,HTTPCommands.iot_headers,json.dumps(rfid_subscription))
	#HTTPCommands.sendRequest("POST",url_sub,HTTPCommands.iot_headers,json.dumps(nextTask_subscription))

	print("Start server ...", flush=True)
	httpd = HTTPServer(("", 40000), SimpleHTTPRequestHandler)
	httpd.serve_forever()

if __name__ == "__main__":
		main()
