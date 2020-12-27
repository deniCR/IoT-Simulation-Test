import requests
import os

host_url = "http://" + os.environ['FIWARE_IP_ADDRESS']
orion_url = host_url + ":" + os.environ['FIWARE_PORT_ADDRESS']
entities_url = orion_url + "/v2/entities"

agent_broker_url = host_url + ":4041/iot"
agent_device_url = host_url + ":7896/iot"

#Service ...
cbroker = "http://orion:" + os.environ['FIWARE_PORT_ADDRESS']

up_headers = {
	'Content-Type': 'text/plain'
}
entities_headers = {
	'fiware-service': 'openiot',
	'fiware-servicepath': '/',
  	'Content-Type': 'application/json'
}
iot_headers = {
	'fiware-service': 'openiot',
	'fiware-servicepath': '/',
	'Content-Type': 'application/json'
}
headers_get_iot = {
	'fiware-service': 'openiot',
	'fiware-servicepath': '/'
}

def sendRequest(command, url, headers={}, payload={}):
	try:
		print(command,url,headers,payload)
		response = requests.request(command, url, headers=headers, data = payload)

		#if response.status_code > 300:
		#	response.raise_for_status()
		return response.text,response.headers
	except requests.exceptions.HTTPError as errh:
			print ("Http Error:",errh)
	except requests.exceptions.ConnectionError as errc:
			print ("Error Connecting:",errc)
	except requests.exceptions.Timeout as errt:
			print ("Timeout Error:",errt)
	except requests.exceptions.RequestException as err:
			print ("OOps: Something Else",err)