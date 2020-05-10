from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
import requests

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
			"url": "http://localhost:8080" }
	},
	"throttling": 5
}
headers = {
  'Content-Type': 'application/json',
  'fiware-service': 'openiot',
  'fiware-servicepath': '/',
  'Content-Type': 'text/plain'
}

def post(url,headers,payload):
	try:
		response = requests.request("POST", url, headers=headers, data = payload)
		#response.raise_for_status()
		print(response.text.encode('utf8'))
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
        #self.wfile.write(b'Hello, world!')

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        self.send_response(200)
        self.end_headers()

        response = BytesIO()
        response.write(b'This is POST request. ')
        response.write(b'Received: ')
        response.write(body)
        self.wfile.write(response.getvalue())

        #if()

def main():
	post(url,headers,json.dumps(payload))
	httpd = HTTPServer(('localhost', 8080), SimpleHTTPRequestHandler)
	httpd.serve_forever()

if __name__ == "__main__":
		main()