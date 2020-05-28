import requests
import json

host = "http://192.168.2.108"
orion = host + ":1026"
entities_url = orion + "/v2/entities"
entities_headers = {
	'fiware-service': 'openiot',
	'fiware-servicepath': '/',
  'Content-Type': 'application/json'
}
up_headers = {
	'Content-Type': 'text/plain'
}

cbroker = "http://orion:1026"

iot_agent = host + ":4041/iot"
agent_reciver = host + ":7896/iot"
iot_headers = {
	'fiware-service': 'openiot',
	'fiware-servicepath': '/',
	'Content-Type': 'application/json'
}
headers_get_iot = {
	'fiware-service': 'openiot',
	'fiware-servicepath': '/'
}

ul_headers = {
	'Content-Type': 'text/plain'
}

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

def patch(url,headers,payload):
	try:
		response = requests.request("PATCH", url, headers=headers, data = payload)
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

def delete(url, headers={}):
	try:
		response = requests.request("DELETE", url, headers=headers, data = {})
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