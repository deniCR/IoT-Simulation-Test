from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
import requests
import json

url = "http://localhost:1026/v2/subscriptions/"
payload = {
	"description": "Notify Server of all RFID context changes",
	"subject": { 
		"entities": [
			{ "idPattern": ".*" , "type": "RFIDSensor"} 
			] 
	},
	"notification": {
		"http": {
			"url": "http://localhost:8001" }
	},
	"throttling": 5
}
headers = {
  'Content-Type': 'application/json'
}


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

	def do_POST(self):
		print("Notification received!!!")
		content_length = int(self.headers['Content-Length'])
		body = self.rfile.read(content_length)
		self.send_response(200)
		self.end_headers()
		print(body)

def main():
	httpd = HTTPServer(('192.168.2.151', 40001), SimpleHTTPRequestHandler)
	httpd.serve_forever()

if __name__ == "__main__":
		main()