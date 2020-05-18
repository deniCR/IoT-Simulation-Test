import requests
import json

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