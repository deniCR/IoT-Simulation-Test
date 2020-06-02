import json
import random
from time import sleep
from termcolor import colored

from . import HTTPCommands as HTTP
from . import Entities
from .Entities import Entity
from .Entities import Null

class Device():
	def __init__(self, id, type, protocol, apikey, ref):

		self.json_entity = {}

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

		self.attrs = []
		self.attrs.append(attributes)

		static_attributes = {}
		static_attributes["name"] = "refStation"
		static_attributes["type"] = "Relationship"
		static_attributes["value"] = self.ref

		self.st_attrs = []
		self.st_attrs.append(static_attributes)
	
		device["attributes"] = []
		device["attributes"].append(attributes)
		device["static_attributes"] = []
		device["static_attributes"].append(static_attributes)

		self.json_entity["devices"].append(device)

	#def add_properties(self):

	def sendData(self):
		url=HTTP.agent_device_url+"/d?k="+self.apikey+"&i="+self.device_id
		data = random.random()*100
		payload= self.attrs[0]["object_id"] + "|" + str(data)
		HTTP.sendRequest("POST",url,HTTP.up_headers,payload)

	def sendData(self, payload):
		url=HTTP.agent_device_url+"/d?k="+self.apikey+"&i="+self.device_id
		HTTP.sendRequest("POST",url,HTTP.up_headers,payload)

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

		response = HTTP.sendRequest("GET",entity_url,HTTP.iot_headers)

		if "device_id" in response:
			if len(self.json_entity["devices"]) == 1:
				self.json_entity["devices"][0] = json.loads(response)
			else:
				self.json_entity["devices"].append(json.loads(response))

	#Verify if the device_id is already registered on the iot-agent
	def exists(self):
		entity_url = HTTP.agent_broker_url + "/devices/" + self.device_id + "/?options=keyValues&attrs=type"

		#Simple get of the entity, if the response is empty the entity don't exist in the broker
		response = json.loads(HTTP.sendRequest("GET",entity_url,HTTP.headers_get_iot))
	
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

	def toString(self):
		return "Device: " + self.entity_type + " - " + self.device_id

class TempSensor(Device):
	def __init__(self, id, protocol, apikey, ref):
		super().__init__(id, "TemperatureSensor", protocol, apikey, ref)

		self.attrs[0]["type"] = "Float"
		self.json_entity["devices"][0]["attributes"][0] = self.attrs[0]

class HumSensor(Device):
	def __init__(self, id, protocol, apikey, ref):
		super().__init__(id, "HumiditySensor", protocol, apikey, ref)


class LightSensor(Device):
	def __init__(self, id, protocol, apikey, ref):
		super().__init__(id, "LightSensor", protocol, apikey, ref)


class CO2Sensor(Device):
	def __init__(self, id, protocol, apikey, ref):
		super().__init__(id, "CO2Sensor", protocol, apikey, ref)


class weightSensor (Device):
	def __init__(self, id, protocol, apikey, ref):
		super().__init__(id, "WeightSensor", protocol, apikey, ref)


class MotionSensor (Device):
	def __init__(self, id, protocol, apikey, ref):
		super().__init__(id, "MotionSensor", protocol, apikey, ref)

		attributes = {}
		attributes["object_id"] = "t"
		attributes["name"] = "time"
		attributes["type"] = "DataTime"

		self.attrs.append(attributes)

		self.json_entity["devices"][0]["attributes"].append(attributes)

class RFIDSensor(Device):
	def __init__(self, id, protocol, apikey, ref):
		super().__init__(id, "RFIDSensor", protocol, apikey, ref)
		
		attributes = {}
		attributes["object_id"] = "t"
		attributes["name"] = "time"
		attributes["type"] = "DataTime"

		self.attrs.append(attributes)

		self.json_entity["devices"][0]["attributes"].append(attributes)

	def sendData(self, code):
		payload="r|"+code
		super().sendData(payload)

class Button(Device):
	def __init__(self, id, protocol, apikey, ref):
		super().__init__(id, "Button", protocol, apikey, ref)
		
		attributes = {}
		attributes["object_id"] = "b"
		attributes["name"] = "Button"
		attributes["type"] = "Text"

		self.attrs[0] = attributes

		self.json_entity["devices"][0]["attributes"][0] = attributes

	def sendData(self, code):
		payload="b|" + code
		super().sendData(payload)
		print(colored("Button post data: ","blue") + code)

	def nextTask(self):
		self.sendData("Stop")

	def initTask(self):
		self.sendData("Start")

class Led(Device):
	def __init__(self, id, protocol, apikey, ref):
		super().__init__(id, "Led", protocol, apikey, ref)
		
		self.state = "Off"
		state = {}
		state["object_id"] = "s"
		state["name"] = "State"
		state["type"] = "Text"

		self.attrs[0] = state

		self.json_entity["devices"][0]["attributes"][0] = state

		self.color = "None"
		attributes = {}
		attributes["object_id"] = "c"
		attributes["name"] = "Color"
		attributes["type"] = "Text"

		self.attrs.append(attributes)

		self.json_entity["devices"][0]["attributes"].append(attributes)

		device = self.json_entity["devices"][0]

		device["transport"] = "HTTP"
		device["endpoint"] = "http://192.168.2.151:40001/iot/" + self.device_id
		device["state"] = "Off"
		device["color"] = "None"

		command_red = {}
		command_red["name"] = "Red"
		command_red["type"] = "Command"

		command_green = {}
		command_green["name"] = "Green"
		command_green["type"] = "Command"

		command_off = {}
		command_off["name"] = "Off"
		command_off["type"] = "Command"

		device["commands"] = []
		device["commands"].append(command_red)
		device["commands"].append(command_green)
		device["commands"].append(command_off)

	def sendData(self):
		url=HTTP.agent_device_url+"/d?k="+self.apikey+"&i="+self.device_id
		payload="s|" + self.state + "|c|" + self.color
		print(colored("Led post data: ", "blue") + self.state +" "+ self.color, flush=True)
		HTTP.sendRequest("POST",url,HTTP.up_headers,payload)

	def execCommand(self, command):
		if command == 'Red':
			self.state = "On"
			self.color = "Red"
			self.sendData()
			pass
		if command == 'Green':
			self.state = "On"
			self.color = "Green"
			self.sendData()
			pass
		if command == 'Off':
			self.state = "Off"
			self.color = "None"
			self.sendData()
			pass