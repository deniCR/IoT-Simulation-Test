import json
import random
from datetime import datetime, timedelta
from time import sleep
from termcolor import colored

from . import HTTPCommands as HTTP
from . import Entities

import Classes.Entities as Entities

Null = "Null"

class Device():
	def __init__(self, id, type, protocol, apikey, ref):

		self.json_entity = {}

		self.id = str(id)
		self.device_id = type[0].lower() + type[1:] + str(id)	
		self.entity_type = type
		self.entity_name = "urn:ngsi-ld:" + type + ":" + str(id)
		self.protocol = protocol
		self.agent_url = HTTP.agent_broker_url + "/devices"
		self.apikey = apikey
		self.ref = ref

		self.json_entity["devices"] = []

		device = {}
		device["device_id"] = self.device_id
		device["entity_name"] = self.entity_name
		device["entity_type"] = self.entity_type
		device["protocol"] = self.protocol

		attributes = {}
		attributes["object_id"] = type[0].lower()
		attributes["name"] = (type).replace('Sensor','')
		attributes["type"] = "Integer"

		static_attributes = {}
		static_attributes["name"] = "refStation"
		static_attributes["type"] = "Relationship"
		static_attributes["value"] = self.ref
	
		device["attributes"] = []
		device["attributes"].append(attributes)
		device["static_attributes"] = []
		device["static_attributes"].append(static_attributes)

		self.json_entity["devices"].append(device)

	def getID(self):
		return self.id

	def sendData(self, payload=Null):
		url=HTTP.agent_device_url+"/d?k="+self.apikey+"&i="+self.device_id
		data = random.random()*100
		if payload == Null:
			payload = self.json_entity["devices"][0]["attributes"][0]["object_id"] + "|" + str(data)
		HTTP.sendRequest("POST",url,HTTP.up_headers,payload)

	#def sendData(self, payload):
	#	url=HTTP.agent_device_url+"/d?k="+self.apikey+"&i="+self.device_id
	#	HTTP.sendRequest("POST",url,HTTP.up_headers,payload)

	def provision(self):
		if not(self.exists()):
			url = self.agent_url
			print(colored("Device provision: ", "green") + str(self.device_id))
			HTTP.sendRequest("POST",url,HTTP.iot_headers,json.dumps(self.json_entity))
			return True
		else:
			print(colored("Warning - (Duplicate): ","red"),"The device already exists in the broker ...")
			return False

	#Load data from the iot-agent
	def get(self, device_id):
		self.device_id = device_id
		entity_url = HTTP.agent_broker_url + "/devices/" + self.device_id

		response, headers = HTTP.sendRequest("GET",entity_url,HTTP.iot_headers)

		if "device_id" in response:
			if len(self.json_entity["devices"]) == 1:
				self.json_entity["devices"][0] = json.loads(response)
			else:
				self.json_entity["devices"].append(json.loads(response))

	#Verify if the device_id is registered on the iot-agent
	def exists(self):
		entity_url = HTTP.agent_broker_url + "/devices/" + self.device_id + "/?options=keyValues&attrs=type"

		#Simple get of the entity, if the response is empty the entity don't exist in the broker
		response = json.loads(HTTP.sendRequest("GET",entity_url,HTTP.headers_get_iot)[0])
	
		if self.entity_name in response.values():
				return True
		return False

	#Deletes the device form the iot-agent AND the broker
	def delete(self):
		#Iot-agent
		entity_url = HTTP.agent_broker_url + '/devices/' + self.device_id
		headers = HTTP.iot_headers
		HTTP.sendRequest("DELETE",entity_url, headers)

		#Broker
		entity_url = HTTP.entities_url + "/" + self.entity_name
		HTTP.sendRequest("DELETE",entity_url, HTTP.headers_get_iot)

	def __str__(self):
		return "Device: " + self.entity_type + " - " + self.device_id

class ProgressSensor(Device):
	def __init__(self, protocol=Null, apikey=Null, ref=Null, workcenter_id=Null, operationNumber=Null, progress=Null, timeStamp=Null):

		self.id = str(workcenter_id)
		super().__init__(workcenter_id, "ProgressSensor", protocol, apikey, ref)

		self.progress = progress
		device = {}
		static_attributes = {}
		static_attributes["name"] = "workcenter_id"
		static_attributes["type"] = "Text"
		static_attributes["value"] = workcenter_id

		self.json_entity["devices"][0]["static_attributes"].append(static_attributes)

		static_attributes_2 = {}
		static_attributes_2["name"] = "operationNumber"
		static_attributes_2["type"] = "Text"
		static_attributes_2["value"] = operationNumber

		self.json_entity["devices"][0]["static_attributes"].append(static_attributes_2)

		static_attributes_3 = {}
		static_attributes_3["name"] = "progress"
		static_attributes_3["type"] = "Text"
		static_attributes_3["value"] = progress

		self.json_entity["devices"][0]["static_attributes"].append(static_attributes_3)

		if timeStamp != Null:
			timeStamp_aux = datetime.strptime(timeStamp, '%Y-%m-%d %H:%M:%S.%f%z')
		else:
			timeStamp_aux = datetime.now()

		static_attributes_4 = {}
		static_attributes_4["name"] = "timeStamp"
		static_attributes_4["type"] = "Numeric"
		static_attributes_4["value"] = timeStamp_aux.timestamp()

		self.json_entity["devices"][0]["static_attributes"].append(static_attributes_4)

	def loadDBEntry(self,protocol,apikey,ref,row):
		if 	"workcenter_id" in row and row["workcenter_id"]:
			self.__init__(protocol, apikey, ref, row["workcenter_id"], row["operationnumber"], row["progress"], row["timestamp"])
			return True
		else:
			return False

	def sendData(self):
		print("Deive: " + self.id + " progress: " + str(self.progress))
		payload="p|"+str(self.progress)
		super().sendData(payload)

