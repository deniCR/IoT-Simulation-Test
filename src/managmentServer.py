#!/usr/bin/env python3

from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
from time import sleep
import requests
import json

url = "http://orion:1026/v2/subscriptions/"
rfid_subscription = {
	"description": "Notify Server of all RFID context changes",
	"subject": { 
		"entities": [{"idPattern": ".*", "type": "RFIDSensor"}],
		"watchAttributes": ["RFID"],
		"q": "RFID!=\"\""
	},
	"notification": {
		"http": {
			"url": "http://managment:40000/notify/RFID",
			"accept": "application/json"
        },
        "attributes": ["RFID","refStation"],
        "attrsFormat": "keyValues"
	},
}
headers = {
  	'fiware-service': 'openiot',
  	'fiware-servicepath': '/',
	'Content-Type': 'application/json'
}
headers_put = {
	'Content-Type': 'text/plain'
}

lastrequest=""

def get(url,headers,payload):
	try:
		response = requests.request("GET", url, headers=headers, data = payload)
		#response.raise_for_status()
		return response.text
	except requests.exceptions.HTTPError as errh:
			print ("Http Error:",errh)
	except requests.exceptions.ConnectionError as errc:
			print ("Error Connecting:",errc)
	except requests.exceptions.Timeout as errt:
			print ("Timeout Error:",errt)
	except requests.exceptions.RequestException as err:
			print ("OOps: Something Else",err)

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

def post(url,headers,payload):
	try:
		response = requests.request("POST", url, headers=headers, data = payload)
		#response.raise_for_status()
		print(response.text.encode('utf8'), flush=True)
	except requests.exceptions.HTTPError as errh:
			print ("Http Error:",errh)
	except requests.exceptions.ConnectionError as errc:
			print ("Error Connecting:",errc)
	except requests.exceptions.Timeout as errt:
			print ("Timeout Error:",errt)
	except requests.exceptions.RequestException as err:
			print ("OOps: Something Else",err)

def put(url,headers,payload):
	try:
		response = requests.request("PUT", url, headers=headers, data = payload)
		#response.raise_for_status()
		print(response.text.encode('utf8'), flush=True)
	except requests.exceptions.HTTPError as errh:
			print ("Http Error:",errh)
	except requests.exceptions.ConnectionError as errc:
			print ("Error Connecting:",errc)
	except requests.exceptions.Timeout as errt:
			print ("Timeout Error:",errt)
	except requests.exceptions.RequestException as err:
			print ("OOps: Something Else",err)


def processRFIDNotification(body):
	entities_url = "http://orion:1026/v2/entities"
	notification = json.loads(body)

	#if "data"

	for r in notification["data"]:
		if r["RFID"]!=" ":
			update_processState = "\"In progress\"" 
			pass
		else :
			update_processState = "\"Stopped\"" 
			pass
		entity_id = r["refStation"]
		entity_url = entities_url + "/" + entity_id
		print("\n" + entity_id + "\n")

		atribute_url = entity_url + "/attrs/processState/value"
		print(atribute_url)
		put(atribute_url,headers_put,update_processState)



class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        print("Notification recived!!!\n", flush=True)

        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)

        self.send_response(200)
        self.end_headers()

        json_text = body.decode('utf8')
        print(json.dumps(json_text,indent=2), flush=True)

        if self.path=='/notify/RFID':
        	processRFIDNotification(body)
        	pass

def main():
	#print(json.dumps(headers, indent=2))
	#print(json.dumps(payload, indent=2))
	wait4Service()
	print("The Service has been created!")
	post(url,headers,json.dumps(rfid_subscription))
	print("Start server ...", flush=True)
	httpd = HTTPServer(("", 40000), SimpleHTTPRequestHandler)
	httpd.serve_forever()

if __name__ == "__main__":
		main()
