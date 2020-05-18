import json
import random

from . import HTTPCommands

cbroker = "http://orion:1026"
host = "http://192.168.2.108"
orion = host + ":1026"
iot_agent = host + ":4041/iot"
agent_reciver = host + ":7896/iot"
iot_headers = {
	'fiware-service': 'openiot',
	'fiware-servicepath': '/',
	'Content-Type': 'application/json'
}
ul_headers = {
	'Content-Type': 'text/plain'
}
entities_headers = {
  'Content-Type': 'application/json',
  'Content-Type': 'text/plain'
}

class Worker:
	def __init__(self,id, name, rfidCode, rfidSensor, button):
		self.cbroker = cbroker
		self.entity_type = "Worker"
		self.entity_id = id
		self.entity_name = name
		self.entity_rfidCode = rfidCode
		self.broker_url = orion + "/v2/entities"
		self.payload = {
				"Worker": [
					{
						"type": self.entity_type,
						"id": self.entity_id,
						"rfidCode": self.entity_rfidCode,
						"name": self.entity_name
					}
				]
		}
		self.rfidSensor = rfidSensor
		self.button = button

	def provision(self):
		url = self.broker_url
		HTTPCommands.post(url,entities_headers,json.dumps(self.payload))
		self.rfidSensor.provision()
		self.button.provision()
		self.init_script()

	def init_script(self):
		self.rfidSensor.send_data()

	def next_task(self):
		self.button.send_data()

	def toString(self):
		return "Worker: " + str(self.entity_id) + " - " + self.entity_rfidCode

class Service:
	def __init__(self, cbroker, apikey, entity_type, resource):
		self.cbroker = cbroker
		self.apikey = apikey
		self.entity_type = entity_type
		self.resource = resource
		self.agent_url = iot_agent + "/services"
		self.payload = {
				 "services": [
					 {
						 "apikey":      self.apikey,
						 "cbroker":     self.cbroker,
						 "entity_type": self.entity_type,
						 "resource":    self.resource
					 }
				 ]
		}

	def provision(self):
		url = self.agent_url
		HTTPCommands.post(url,iot_headers,json.dumps(self.payload))

class Device:
	def __init__(self, id, type, name, protocol, apikey):
		self.device_id = id
		self.entity_type = type
		self.entity_name = "urn:ngsi-ld:" + name
		self.protocol = protocol
		self.agent_url = iot_agent + "/devices"
		self.apikey = apikey
		self.payload = {
			 "devices": [
				 {
					 "device_id":   self.device_id,
					 "entity_name": self.entity_name,
					 "entity_type": self.entity_type,
					 "protocol":    self.protocol,
				}
				]
			}

	#def add_properties(self):

	def send_data(self):
		url=agent_reciver+"/d?k="+self.apikey+"&i="+self.device_id
		data = random.random()*100
		payload="t|"+str(data)
		HTTPCommands.post(url,ul_headers,payload)


	def provision(self):
		url = self.agent_url
		HTTPCommands.post(url,iot_headers,json.dumps(self.payload))

	def toString(self):
		return "Device: " + self.entity_type + " - " + self.device_id

class TempSensor(Device):
	def __init__(self, id, protocol, apikey, ref):
		super().__init__("temperatureSensor"+str(id), "TemperatureSensor", "TemperatureSensor:"+str(id), protocol, apikey)
		self.ref = ref
		self.payload = {
			 "devices": [
				 {
					 "device_id":   self.device_id,
					 "entity_name": self.entity_name,
					 "entity_type": self.entity_type,
					 "protocol":    self.protocol,
					 "attributes": [
							{ "object_id": "t", "name": "temperature", "type": "Float" }
						],
						"static_attributes": [
							{ "name":"refRequirement", "type": "Relationship", "value": self.ref}
						]
				}
				]
			}

class HumSensor(Device):
	def __init__(self, id, protocol, apikey, ref):
		super().__init__("humiditySensor"+str(id), "HumiditySensor", "HumiditySensor:"+str(id), protocol, apikey)
		self.ref = ref
		self.payload = {
			 "devices": [
				 {
					 "device_id":   self.device_id,
					 "entity_name": self.entity_name,
					 "entity_type": self.entity_type,
					 "protocol":    self.protocol,
					 "attributes": [
							{ "object_id": "h", "name": "humidity", "type": "Float" }
						],
						"static_attributes": [
							{ "name":"refRequirement", "type": "Relationship", "value": self.ref}
						]
				}
				]
			}

class LightSensor(Device):
	def __init__(self, id, protocol, apikey, ref):
		super().__init__("lightSensor"+str(id), "LightSensor", "LightSensor:"+str(id), protocol, apikey)
		self.ref = ref
		self.payload = {
			 "devices": [
				 {
					 "device_id":   self.device_id,
					 "entity_name": self.entity_name,
					 "entity_type": self.entity_type,
					 "protocol":    self.protocol,
					 "attributes": [
							{ "object_id": "l", "name": "Light", "type": "Integer" }
						],
						"static_attributes": [
							{ "name":"refRequirement", "type": "Relationship", "value": self.ref}
						]
				}
				]
			}

class CO2Sensor(Device):
	def __init__(self, id, protocol, apikey, ref):
		super().__init__("co2sensor"+str(id), "CO2Sensor", "CO2Sensor:"+str(id), protocol, apikey)
		self.ref = ref
		self.payload = {
			 "devices": [
				 {
					 "device_id":   self.device_id,
					 "entity_name": self.entity_name,
					 "entity_type": self.entity_type,
					 "protocol":    self.protocol,
					 "attributes": [
							{ "object_id": "c", "name": "CO2", "type": "Integer" }
						],
						"static_attributes": [
							{ "name":"refRequirement", "type": "Relationship", "value": self.ref}
						]
				}
				]
			}

class weightSensor (Device):
	def __init__(self, id, protocol, apikey, ref):
		super().__init__("weightSensor"+str(id), "WeightSensor", "WeightSensor:"+str(id), protocol, apikey)
		self.ref = ref
		self.payload = {
			 "devices": [
				 {
					 "device_id":   self.device_id,
					 "entity_name": self.entity_name,
					 "entity_type": self.entity_type,
					 "protocol":    self.protocol,
					 "attributes": [
							{ "object_id": "w", "name": "Weight", "type": "Float" }
						],
						"static_attributes": [
						
							{ "name":"refRequirement", "type": "Relationship", "value": self.ref}
						]
				}
				]
			}

class MotionSensor (Device):
	def __init__(self, id, protocol, apikey, ref):
		super().__init__("motionSensor"+str(id), "MotionSensor", "MotionSensor:"+str(id), protocol, apikey)
		self.ref = ref
		self.payload = {
			 "devices": [
				 {
					 "device_id":   self.device_id,
					 "entity_name": self.entity_name,
					 "entity_type": self.entity_type,
					 "protocol":    self.protocol,
					 "attributes": [
							{ "object_id": "m", "name": "Motion", "type": "Integer" },
							{ "object_id": "t", "name": "Time", "type": "DataTime"}

						],
						"static_attributes": [
							{ "name":"refRequirement", "type": "Relationship", "value": self.ref}
						]
				}
				]
			}

class RFIDSensor (Device):
	def __init__(self, id, protocol, apikey, ref):
		super().__init__("rfidSensor"+str(id), "RFIDSensor", "RFIDSensor:"+str(id), protocol, apikey)
		self.ref = ref
		self.payload = {
			 "devices": [
				 {
					 "device_id":   self.device_id,
					 "entity_name": self.entity_name,
					 "entity_type": self.entity_type,
					 "protocol":    self.protocol,
					 "attributes": [
							{ "object_id": "r", "name": "RFID", "type": "Integer" },
							{ "object_id": "t", "name": "Time", "type": "DataTime"}

						],
						"static_attributes": [
							{ "name":"refStation", "type": "Relationship", "value": self.ref}
						]
				}
				]
			}

	def send_data(self):
		url=agent_reciver+"/d?k="+self.apikey+"&i="+self.device_id
		data = int(random.random()*100)
		payload="r|"+"fshuidaohfeiuhqw"+str(data)
		HTTPCommands.post(url,ul_headers,payload)

class Button (Device):
	def __init__(self, id, protocol, apikey, ref):
		super().__init__("button"+str(id), "Button", "Button:"+str(id), protocol, apikey)
		self.ref = ref
		self.payload = {
			 "devices": [
				 {
					 "device_id":   self.device_id,
					 "entity_name": self.entity_name,
					 "entity_type": self.entity_type,
					 "protocol":    self.protocol,
					 "attributes": [
							{ "object_id": "p", "name": "Press", "type": "Integer" },
							{ "object_id": "t", "name": "Time", "type": "DataTime"}
						],
						"static_attributes": [
							{ "name":"refStation", "type": "Relationship", "value": self.ref}
						]
				}
				]
			}

class Led (Device):
	def __init__(self, id, protocol, apikey, ref):
		super().__init__("led"+str(id), "Led", "Led:"+str(id), protocol, apikey)
		self.ref = ref
		self.endpoint = "http://192.168.2.151:40001/iot/led" + str(id)
		self.payload = {
			 "devices": [
				 {
					 "device_id":   self.device_id,
					 "entity_name": self.entity_name,
					 "entity_type": self.entity_type,
					 "protocol":    self.protocol,
					 "transport": "HTTP",
      				 "endpoint": self.endpoint,
					 "commands": [
							{ "name": "Red", "type": "Command" },
							{ "name": "Green", "type": "Command" }
						],
						"static_attributes": [
							{ "name":"refStation", "type": "Relationship", "value": self.ref}
						]
				}
				]
			}