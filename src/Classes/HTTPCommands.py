import requests
import json

host_url = "http://192.168.2.108"
orion_url = host_url + ":1026"
entities_url = orion_url + "/v2/entities"

agent_broker_url = host_url + ":4041/iot"
agent_device_url = host_url + ":7896/iot"

#Service ...
cbroker = "http://orion:1026"

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
		response = requests.request(command, url, headers=headers, data = payload)
		#if response.status_code > 300:
		#	response.raise_for_status()
		return response.text
	except requests.exceptions.HTTPError as errh:
			print ("Http Error:",errh)
	except requests.exceptions.ConnectionError as errc:
			print ("Error Connecting:",errc)
	except requests.exceptions.Timeout as errt:
			print ("Timeout Error:",errt)
	except requests.exceptions.RequestException as err:
			print ("OOps: Something Else",err)