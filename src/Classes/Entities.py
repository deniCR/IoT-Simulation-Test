import json
from time import sleep
from termcolor import colored
import datetime

from . import HTTPCommands

Null = "Null"

class Entity:
	def __init__(self,id=Null,type=Null,name=Null,description=Null):
		self.id = "urn:ngsi-ld:" + type + ":" + str(id)
		self.type = type
		self.name = {}
		self.name["type"] = "Text"
		self.name["value"] = name
		self.description = {}
		self.description["type"] = "Text"
		self.description["value"] = description
		self.attrs = []

		self.json_entity = {}
		if id!=Null:
			self.json_entity["id"] = self.id
		if type!=Null:
			self.json_entity["type"] = self.type
		if name!=Null:
			self.json_entity["name"] = self.name
		if description!=Null:
			self.json_entity["description"] = self.description

	def getID(self):
		id = self.json_entity["id"]
		return id

	def load(self, json):
		json_entity = json.dumps(json)

		self.description = Null
		self.name = Null

		if "id" in json:
			self.id = json["id"]
		if "type" in json:
			self.type = json["type"]
		if "name" in json:
			self.name = json["name"]
		if "description" in json:
			self.description = json["description"]

	def addAttr(self, name, type, value):
		new_attr = {}
		new_attr["type"] = type
		new_attr["value"] = value

		if name in self.attrs:
			self.attrs[name]=new_attr
		else:	
			self.attrs.append(new_attr)
		
		self.json_entity[name]=new_attr

	def get(self, entity_id=Null):
		if entity_id != Null:
			self.id = entity_id
		entity_url = HTTPCommands.entities_url + "/" + self.id

		#print(entity_url)

		response = HTTPCommands.get(entity_url,HTTPCommands.headers_get_iot,{})
		self.json_entity = json.loads(response)

	def provision(self):
		if not(self.exists()):
			print(self.type + " provision: " + self.id)
			#print(self.json_entity)

			#Provision of the "entire" entity (id+type+attrs)
			HTTPCommands.post(HTTPCommands.entities_url,HTTPCommands.entities_headers,json.dumps(self.json_entity))
			print(colored("Sucesses: ","green"))
		else:
			print(colored("Warning - (Duplicate): ","red"),"The entity already exists in the broker ...")

	#def updateValue(self,attribute,new_value):

	#Updates one (doesn't append new attributes)
	def update(self,listofchanges):
		deleteAttrs = []

		#Change the values of the respective keys ...
		for key in listofchanges:
			if key in self.json_entity:
				self.json_entity[key] = listofchanges[key]
			else:
				deleteAttrs.append(key)

		#Delete the attrs that aren't present in the object
		for key in deleteAttrs:
			del listofchanges[key]

		#Update only the values that correspond to the actual attrs
		if len(listofchanges) > 0:
			entity_url = HTTPCommands.entities_url + "/" + self.id
			atribute_url = entity_url + "/attrs/?options=keyValues"

			#print("\n" + atribute_url + " " + json.dumps(listofchanges))

			HTTPCommands.patch(atribute_url,HTTPCommands.entities_headers,json.dumps(listofchanges))

		self.get()

	def exists(self):
		entity_url = HTTPCommands.entities_url + "/" + self.id + "/?options=keyValues&attrs=type"
		
		#Simple get of the entity, if the response is empty the entity don't exist in the broker
		response = HTTPCommands.get(entity_url,HTTPCommands.headers_get_iot,{})
		
		#print("\n" + response)

		if self.id in response:
				return True
		return False

	def delete(self):
		entity_url = HTTPCommands.entities_url + "/" + self.id
		#The delete command doesn't need headers or the data body ... just the url
		HTTPCommands.delete(entity_url)

	def toString(self):
		return json.dumps(self.json_entity,indent=2)

#class Terminal

class Worker(Entity):
	def __init__(self,id=Null, name=Null, rfidCode=Null, rfidSensor=Null, button=Null, led=Null):
		super().__init__(id=id,type="Worker",name=name,description=Null)
		self.addAttr("rfidCode","Text",rfidCode)
		self.entity_rfidCode = rfidCode

		#Sensors
		self.rfidSensor = rfidSensor
		self.button = button
		self.led = led

	def provision(self):
		super().provision()

		#Sensors provision
		self.rfidSensor.provision()
		self.button.provision()
		self.led.provision()
		self.led.send_data()

	def init_script(self):
		self.rfidSensor.send_data(self.entity_rfidCode)

		#Wait until led changes color - Off, Red or Green
		while self.led.color=='None':
			sleep(1)

		#The command has been received 
		self.led.execCommand("Off")

	def next_task(self):
		self.button.next_task()
		#Wait until led changes color - Off, Red or Green
		while self.led.color=='None':
			sleep(0.25)
			pass

		#The command has been received 
		self.led.execCommand("Off")

	def getByRFIDCode(self, rfidCode):

		entity_url = HTTPCommands.entities_url + "/?type=Worker&q=rfidCode=='" +rfidCode+ "'&options=keyValues&attrs=." 

		#print(entity_url)

		response = HTTPCommands.get(entity_url,HTTPCommands.headers_get_iot,{})
		json_response = json.loads(response)

		if len(json_response) > 0:
			if "id" in json_response[0]:
				worker_ref = json_response[0]["id"]
				self.get(worker_ref)

	def toString(self):
		return "Worker: " + str(self.id) + " - " + self.entity_rfidCode

class Station(Entity):
	def __init__(self,id=Null,name=Null, description=Null, refPrevious=Null, refFollowing=Null, refScript=Null):
			super().__init__(id=id,type="Station",name=name,description=description)
			self.addAttr("refPrevious","Relationship",refPrevious)
			self.addAttr("refFollowing","Relationship",refFollowing)
			self.addAttr("refScript","Relationship",refScript)
			self.addAttr("Float","CO2","0.0")
			self.addAttr("Float","humidity","0.0")
			self.addAttr("Float","luminosity","0.0")
			self.addAttr("Float","productivity","0.0")
			self.addAttr("Float","temperature","0.0")

	def gePrevious(self):
		previousStation = Station()
		previousStation.get(self.json_entity["refPrevious"]["value"])
		return previousStation

	def getFollowing(self):
		nextStation = Station()
		nextStation.get(self.json_entity["refFollowing"]["value"])
		return nextStation

	def getScript(self):
		script = Script()
		print(self.toString())
		script.get(self.json_entity["refScript"]["value"])
		return script

class Script(Entity):
	def __init__(self,id=Null,name=Null, refStation=Null, refFirst=Null):
			super().__init__(id=id,type="Script",name=name,description=Null)
			self.addAttr("refStation","Relationship",refStation)
			self.addAttr("refFirstTask","Relationship",refFirst)
			self.addAttr("refActualTask","Relationship","") 
			self.addAttr("assemblyTime","Float","0.0")
			self.addAttr("startTime","DataTime","")
			self.addAttr("stopTime","DataTime","")
			self.addAttr("actualProcessState","Float","0.0")
			self.addAttr("taskProcessState","Float","0.0")
			self.addAttr("refWorker","Relationship","")

	#def getStation(self):
	#	station = Station()
	#	station.get(self.json_entity["refStation"]["value"])
	#	return station

	def getByStation(self, refStation):
		#Query: refStation == script_id;
		#		type == LED;
		#		limit == 1;
		# 		attribute == None - . ? - smallest response 
		url = HTTPCommands.entities_url + "/?q=refStation=='" + refStation + "'&type=Script&options=keyValues&attrs=type"
		#print(url)
		response = json.loads(HTTPCommands.get(url, HTTPCommands.headers_get_iot, {}))

		#print("GET Script: " + json.dumps(response))

		#The response contains only one entity
		#	the entity contains the id and type
		if len(response)==1 and len(response[0])==2:
			self.get(response[0]["id"])
			
		return False

	def getFistTask(self):
		firstTask = Task()
		firstTask.get(self.json_entity["refFirstTask"]["value"])
		return firstTask

	def getActualTask(self):
		newtask = Task()
		newtask.get(self.json_entity["refActualTask"]["value"])
		return newtask

	#def getWorker(self):
	#	worker = Worker()
	#	worker.get(self.json_entity["refWorker"]["value"])
	#	return worker

	def getNumTasks(self):
		url = HTTPCommands.entities_url + "/?type=Task&q=refScript==\'" + self.id + "\'&attrs=type&options=values"

		response = HTTPCommands.get(url,HTTPCommands.headers_get_iot,{})

		number_of_tasks = len(json.loads(response))
		return number_of_tasks

	def updateProcessState(self, taskNumber=-1, newTime="now"):
		if taskNumber==-1:
			actualTask = int(self.json_entity["taskNumber"]["value"])-1
		else:
			actualTask=taskNumber

		if actualTask < 0:
			processState = "Stopped"
		else:
			if actualTask == 0:
				processState = "0"
			else:
				processState = str(format(100*(actualTask/self.getNumTasks()), '.3f'))

		#print(processState)

		return processState

	def init_script(self, timeInstant=Null):

		print(colored("\nInit Script"), "green")

		firstTask = self.getFistTask()
		firstTask_ref = firstTask.json_entity["id"]

		new_values = {}
		new_values["refActualTask"] = firstTask_ref
		new_values["taskNumber"] = "1"
		new_values["taskProcessState"] = self.updateProcessState(1)
		if timeInstant != Null:
			new_values["startTime"] = timeInstant
			new_values["stopTime"] = timeInstant

		self.update(new_values)

	def next_task(self, timeInstant):
		actual = self.getActualTask()
		next = actual.getNextTask()
		next_ref = next.json_entity["id"]

		new_values = {}

		#print(self.toString())

		if next_ref == self.json_entity["refFirstTask"]["value"]:
			#Productivity
			actualProfuctivity = float(self.json_entity["productivity"]["value"])
			actualProfuctivity += 1
			new_values["productivity"] = str(format(actualProfuctivity, '.3f'))

			#AVG
			assemblyTime = float(self.json_entity["assemblyTime"]["value"])
			startTime = datetime.datetime.strptime(self.json_entity["startTime"]["value"], "%Y-%m-%dT%H:%M:%S.00Z")
			endTime = datetime.datetime.strptime(self.json_entity["stopTime"]["value"], "%Y-%m-%dT%H:%M:%S.00Z")
			duration = endTime - startTime
			duration_s = duration.total_seconds()
			avgTime = (assemblyTime+duration_s)/2

			new_values["assemblyTime"] = str(format(avgTime, '.3f'))

			self.init_script(timeInstant)
			nextTaskNum = 1
		else:
			actualTaskNum = int(self.json_entity["taskNumber"]["value"])
			nextTaskNum = actualTaskNum + 1

		#Time
		startTime = datetime.datetime.strptime(self.json_entity["startTime"]["value"], "%Y-%m-%dT%H:%M:%S.00Z")
		actualTime = datetime.datetime.utcnow()
		duration = actualTime - startTime
		total_s = duration.total_seconds()
		actualProcessState = 100*(total_s/float(self.json_entity["assemblyTime"]["value"]))

		new_values["refActualTask"] = next_ref
		new_values["taskNumber"] = str(nextTaskNum)
		new_values["taskProcessState"] = self.updateProcessState(nextTaskNum,"now")
		new_values["actualProcessState"] = str(format(actualProcessState, '.3f'))

		self.update(new_values)

	#def end_script(self):


class Task(Entity):
	def __init__(self,id=Null,name=Null, refScript=Null, refNextTask=Null, refRequirements=Null):
			super().__init__(id=id,type="Task",name=name,description=Null)
			self.addAttr("assemblyTime","Float","0.0")
			self.addAttr("startTime","DataTime","")
			self.addAttr("stopTime","DataTime","")
			self.addAttr("refScript","Relationship",refScript)
			self.addAttr("refRequirements","Relationship",refRequirements)
			self.addAttr("refNextTask","Relationship",refNextTask)

	def getScript(self):
		return Station().get(self.json_entity["refScript"]["value"])

	def getRequirements(self):
		return Requirements().get(self.json_entity["refRequirements"]["value"])

	def getNextTask(self):
		newtask = Task()
		newtask.get(self.json_entity["refNextTask"]["value"])
		return newtask

class Requirements(Entity):
	def __init__(self,id=Null,name=Null, query=Null, refSensor=Null, refStation=Null, max=Null, min=Null):
		super().__init__(id=id,type="Requirements",name=name,description=Null)
		self.addAttr("refDevice","Relationship",refSensors)
		self.addAttr("refStation", "Relationship", refDevice)
		self.addAttr("query", "Query", query)
		self.addAttr("max", "Float", max)
		self.addAttr("min", "Float", min)
		# ????

	def getDevice(self):
		device = Sensor()
		device.get(self.json_entity["refDevice"]["value"])
		return device

	def getStation(self):
		station = Station()
		station.get(self.json_entity["refStation"]["value"])
		return station

class Device(Entity):
	def __init__(self,id=Null,name=Null, description=Null):
		super().__init__(id=id,type="Device",name=name,description=description)

	def get(self, entity_id):
		self.id = entity_id
		entity_url = HTTPCommands.entities_url + "/" + self.id

		#print(entity_url)

		response = HTTPCommands.get(entity_url,HTTPCommands.headers_get_iot,{})
		self.json_entity = json.loads(response)

	def getByStation(self, refStation):
		#Query: refStation == script_id;
		#		type == LED;
		#		limit == 1;
		# 		attribute == None - . ? - smallest response 
		url = HTTPCommands.entities_url + "/?q=refStation=='" + refStation + "'&type=Led&options=keyValues&attrs=type&limit=1"
		#print(url)
		response = json.loads(HTTPCommands.get(url, HTTPCommands.headers_get_iot, {}))

		print("GET LED: " + json.dumps(response))

		#The response contains only one entity
		#	the entity contains the id and type
		if len(response)==1 and len(response[0])==2:
			self.get(response[0]["id"])
			
		return False

	def execCommand(self, command):
		if "id" in self.json_entity:
			if command in self.json_entity:
				if "Command" in self.json_entity[command].values():

					payload = {}
					payload[command] = {}
					payload[command]["type"] = "Command"
					payload[command]["value"] = ""

					print(colored("Send command: ", "green") + command)
					HTTPCommands.patch(HTTPCommands.entities_url + "/" + self.json_entity["id"] + "/attrs",HTTPCommands.iot_headers,json.dumps(payload))
					return True

		print(colored("Error, the command could not be sent: ", "red") + command)
		#print(self.toString())
		return False

class Service(Entity):
	def __init__(self, cbroker, apikey, entity_type, resource):
		super().__init__(id=Null,type=Null,name=Null,description=Null)

		self.entity_type = entity_type
		self.apikey = apikey
		self.resource = resource
		self.services_url = HTTPCommands.iot_agent + "/services"

		self.json_entity["services"] = []

		service = {}
		service["entity_type"] = self.entity_type
		service["apikey"] = self.apikey
		service["cbroker"] = HTTPCommands.cbroker
		service["resource"] = self.resource

		self.json_entity["services"].append(service)

	def provision(self):
		if not(self.exists()):
			url = self.services_url
			print("Service provision: " + self.apikey)
			#print(json.dumps(self.json_entity))
			HTTPCommands.post(url,HTTPCommands.iot_headers,json.dumps(self.json_entity))
		else:
			print(colored("Warning - (Duplicate): ","red"),"The service already exists in the broker ...")

	def exists(self):
		url_services = self.services_url + "/?resource=" + self.resource
		payload_service = {}

		response = HTTPCommands.get(url_services,HTTPCommands.iot_headers,json.dumps(payload_service))
		response_json = json.loads(response)
		count = int(response_json["count"])

		if count > 0:
			for service in response_json["services"]:
				if self.resource in service.values():
					return True
		return False

	def get(self, resource):
		url_services = self.services_url + "/?resource=" + resource
		payload_service = {}

		response = HTTPCommands.get(url_services,HTTPCommands.iot_headers,json.dumps(payload_service))
		response_json = json.loads(response)
		count = int(response_json["count"])

		if count > 0:
			for service in response_json["services"]:
				if resource in service.values():
					del service["_id"]
					del service["__v"]

					self.entity_type = service["entity_type"]
					self.apikey = service["apikey"]
					self.resource = service["resource"]

					self.json_entity["services"] = []
					self.json_entity["services"].append(service)


	def delete(self):
		entity_url = self.services_url + "/?resource=" + self.resource + "&apikey=" + self.apikey

		headers = HTTPCommands.iot_headers
		HTTPCommands.delete(entity_url,headers)
