#!/usr/bin/env python3

from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
import requests
import json

url = "http://orion:1026/v2/subscriptions/"
payload = {
	"description": "Notify Server of all RFID context changes",
	"subject": { 
		"entities": [{"idPattern": ".*", "type": "RFIDSensor"}],
		"watchAttributes": ["RFID"],
		"q": "RFID!=\"\""
	},
	"notification": {
		"http": {
			"url": "http://managment:40000",
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

lastrequest=""

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


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(lastrequest.encode('utf8'))

    def do_POST(self):
        print("Notification recived!!!\n", flush=True)
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        self.send_response(200)
        self.end_headers()

        response = BytesIO()
        response.write(b'This is POST request. ')
        response.write(b'Received: ')
        response.write(body)
        json_text = body.decode('utf8')
        print(json.dumps(json_text,indent=2), flush=True)
        lastrequest=body
        self.wfile.write(response.getvalue())

def main():
	#print(json.dumps(headers, indent=2))
	#print(json.dumps(payload, indent=2))

	post(url,headers,json.dumps(payload))
	print("Start server ...", flush=True)
	httpd = HTTPServer(("", 40000), SimpleHTTPRequestHandler)
	httpd.serve_forever()

if __name__ == "__main__":
		main()
