import json
import random
from time import sleep
from termcolor import colored

from . import HTTPCommands
from . import Entities
from .Entities import Entity
from .Entities import Null

class Device(Entity):
	def __init__(self, id, type, protocol, apikey, ref):
		super().__init__(id=Null,type=Null,name=Null,description=Null)

		self.device_id = type[0].lower() + type[1:] + str(id)	
		self.entity_type = type
		self.entity_name = "urn:ngsi-ld:" + type + ":" + str(id)
		self.protocol = protocol
		self.agent_url = HTTPCommands.iot_agent + "/devices"
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

	def send_data(self):
		url=HTTPCommands.agent_reciver+"/d?k="+self.apikey+"&i="+self.device_id
		data = random.random()*100
		payload= self.attrs[0]["object_id"] + "|" + str(data)
		HTTPCommands.post(url,HTTPCommands.up_headers,payload)

	def send_data(self, payload):
		url=HTTPCommands.agent_reciver+"/d?k="+self.apikey+"&i="+self.device_id
		HTTPCommands.post(url,HTTPCommands.up_headers,payload)

	def provision(self):
		if not(self.exists()):
			url = self.agent_url
			print(colored("Device provision: ", "green") + str(self.device_id))
			#print(self.json_entity)

			HTTPCommands.post(url,HTTPCommands.iot_headers,json.dumps(self.json_entity))
		else:
			print(colored("Warning - (Duplicate): ","red"),"The device already exists in the broker ...")

	def get(self, device_id):
		self.device_id = device_id
		entity_url = HTTPCommands.iot_agent + "/devices/" + self.device_id

		response = HTTPCommands.get(entity_url,HTTPCommands.iot_headers,{})
		self.json_entity["devices"][0] = json.loads(response)

		#print("\n\t" + json.dumps(self.json_entity, indent=2) + "\n")

	def exists(self):
		entity_url = HTTPCommands.iot_agent + "/devices/" + self.device_id + "/?options=keyValues&attrs=type"
		
		headers = {
			'fiware-service': 'openiot',
			'fiware-servicepath': '/'
		}

		#Simple get of the entity, if the response is empty the entity don't exist in the broker
		response = json.loads(HTTPCommands.get(entity_url,headers,{}))

		#print("\n" + json.dumps(response), flush=True)
	
		if self.entity_name in response.values():
				return True
		return False

	#Deletes the device form the iot-agent AND the broker
	def delete(self):
		#Iot-agent
		entity_url = HTTPCommands.iot_agent + '/devices/' + self.device_id

		headers = HTTPCommands.iot_headers
		HTTPCommands.delete(entity_url, headers)

		#Broker
		entity_url = HTTPCommands.entities_url + "/" + self.entity_name

		headers = {
			'fiware-service': 'openiot',
			'fiware-servicepath': '/'
		}
		HTTPCommands.delete(entity_url, headers)

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

	def send_data(self, code):
		payload="r|"+code
		super().send_data(payload)

class Button(Device):
	def __init__(self, id, protocol, apikey, ref):
		super().__init__(id, "Button", protocol, apikey, ref)
		
		attributes = {}
		attributes["object_id"] = "b"
		attributes["name"] = "Button"
		attributes["type"] = "Text"

		self.attrs[0] = attributes

		self.json_entity["devices"][0]["attributes"][0] = attributes

	def send_data(self, code):
		payload="b|" + code
		super().send_data(payload)
		print(colored("Button post data: ","blue") + code)

	def next_task(self):
		self.send_data("Stop")

	def init_task(self):
		self.send_data("Start")

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

	def send_data(self):
		url=HTTPCommands.agent_reciver+"/d?k="+self.apikey+"&i="+self.device_id
		payload="s|" + self.state + "|c|" + self.color
		print(colored("Led post data: ", "blue") + self.state +" "+ self.color, flush=True)
		HTTPCommands.post(url,HTTPCommands.ul_headers,payload)

	def execCommand(self, command):
		if command == 'Red':
			self.state = "On"
			self.color = "Red"
			self.send_data()
			pass
		if command == 'Green':
			self.state = "On"
			self.color = "Green"
			self.send_data()
			pass
		if command == 'Off':
			self.state = "Off"
			self.color = "None"
			self.send_data()
			pass

#class Worker:
#	def __init__(self,id, name, rfidCode, rfidSensor, button, led):
#		self.entity_type = "Worker"
#		self.entity_id = "urn:ngsi-ld:Worker:" + str(id)
#		self.entity_name = name
#		self.entity_rfidCode = rfidCode
#		self.broker_url = HTTPCommands.orion + "/v2/entities"
#		self.payload = {
#						"type": self.entity_type,
#						"id": self.entity_id,
#						"rfidCode": { "type": "Text", "value": self.entity_rfidCode},
#						"name": { "type": "Text", "value": self.entity_name}
#		}
#		self.rfidSensor = rfidSensor
#		self.button = button
#		self.led = led
#
#	def provision(self):
#		print("Work provision: " + self.entity_id)
#		print(json.dumps(self.payload))
#		HTTPCommands.post(self.broker_url,entities_headers,json.dumps(self.payload))
#		self.rfidSensor.provision()
#		self.button.provision()
#		self.led.provision()
#		self.led.send_data()
#		#self.init_script()
#
#	def init_script(self):
#		self.rfidSensor.send_data()
#		#Wait until led changes color - Off, Red or Green
#		while self.led.color=='None':
#			sleep(1)
#
#		print(self.led.color)
#		#if color is red start again > otherwise continue ...
#
#	def next_task(self):
#		self.button.send_data()
#		#Wait until led changes color - Off, Red or Green
#		while self.led.color=='None':
#			sleep(0.25)
#			pass
#
#		print(self.led.color)
#		#if color is red start again > otherwise continue ...
#
#	def toString(self):
#		return "Worker: " + str(self.entity_id) + " - " + self.entity_rfidCode

#class Service:
#	def __init__(self, cbroker, apikey, entity_type, resource):
#		self.cbroker = HTTPCommands.cbroker
#		self.apikey = apikey
#		self.entity_type = entity_type
#		self.resource = resource
#		self.agent_url = HTTPCommands.iot_agent + "/services"
#		self.payload = {
#				 "services": [
#					 {
#						 "apikey":      self.apikey,
#						 "cbroker":     self.cbroker,
#						 "entity_type": self.entity_type,
#						 "resource":    self.resource
#					 }
#				 ]
#		}
#
#	def provision(self):
#		url = self.agent_url
#		print("Service provision: " + self.apikey)
#		HTTPCommands.post(url,HTTPCommands.iot_headers,json.dumps(self.payload))
