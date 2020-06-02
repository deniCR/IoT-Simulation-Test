import json
from time import sleep
from termcolor import colored
import datetime

from . import HTTPCommands as HTTP

Null = "Null"

class Service():
	def __init__(self, cbroker, apikey, entity_type, resource):

		self.json_entity = {}

		self.entity_type = entity_type
		self.apikey = apikey
		self.resource = resource
		self.services_url = HTTP.agent_broker_url + "/services"

		self.json_entity["services"] = []

		service = {}
		service["entity_type"] = self.entity_type
		service["apikey"] = self.apikey
		service["cbroker"] = HTTP.cbroker
		service["resource"] = self.resource

		self.json_entity["services"].append(service)

	def provision(self):
		if not(self.exists()):
			url = self.services_url
			print("Service provision: " + self.apikey)
			HTTP.sendRequest("POST",url,HTTP.iot_headers,json.dumps(self.json_entity))
			return True
		else:
			print(colored("Warning - (Duplicate): ","red"),"The service already exists in the broker ...")
			return False

	def exists(self):
		url_services = self.services_url + "/?resource=" + self.resource
		payload_service = {}

		response = HTTP.sendRequest("GET",url_services,HTTP.iot_headers,json.dumps(payload_service))
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

		response = HTTP.sendRequest("GET",url_services,HTTP.iot_headers,json.dumps(payload_service))
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
					return True
		return False

	def delete(self):
		entity_url = self.services_url + "/?resource=" + self.resource + "&apikey=" + self.apikey

		headers = HTTP.iot_headers
		HTTP.sendRequest("DELETE",entity_url,headers)

class Entity:
	def __init__(self,type,id=Null,name=Null,description=Null):
		self.type = type

		self.json_entity = {}
		self.json_entity["type"] = self.type

		if id!=Null:
			self.id = "urn:ngsi-ld:" + type + ":" + str(id)
			self.json_entity["id"] = self.id
		
		if name!=Null:
			self.addAttr("name","Text",name)
		if description!=Null:
			self.addAttr("description","Text",description)

	#GET functions will return None if the operation isn't successful
	def getID(self):
		if "id" in self.json_entity:
			id = self.json_entity["id"]
			return id
		return None

	def getType(self):
		if "type" in self.json_entity:
			id = self.json_entity["type"]
			return id
		return None

	#Get the attribute value from the json_entity
	def getAttrValue(self, attr):
		if attr in self.json_entity:
			if "value" in self.json_entity[attr]:
				id = self.json_entity[attr]["value"]
				return id
		return None

	#The load function will load all the information from the json object
	def load(self, json):
		json_entity = json.dumps(json)

		if "id" in json:
			self.id = json["id"]
		if "type" in json:
			self.type = json["type"]

	#The addAttr function adds a new attribute to the Entity
	def addAttr(self, name, type, value):
		new_attr = {}
		new_attr["type"] = type
		new_attr["value"] = value
		
		self.json_entity[name]=new_attr

	#The get function will copy the data hold by the broker and load the Entity
	def get(self, entity_id=Null):
		if entity_id != Null:
			self.id = entity_id
		entity_url = HTTP.entities_url + "/" + self.id

		response = HTTP.sendRequest("GET",entity_url,HTTP.headers_get_iot)

		if "type" in response:
			self.json_entity = json.loads(response)
			return True
		return False

	#The provision function will register the entity
	def provision(self):
		if not(self.exists()):
			print(self.type + " provision: " + self.id)

			HTTP.sendRequest("POST",HTTP.entities_url,HTTP.entities_headers,json.dumps(self.json_entity))
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

		#Delete the attributes that aren't present in the object
		for key in deleteAttrs:
			del listofchanges[key]

		#Update only the values that correspond to the current attributes
		if len(listofchanges) > 0:
			entity_url = HTTP.entities_url + "/" + self.id
			atribute_url = entity_url + "/attrs/?options=keyValues"

			HTTP.sendRequest("PATCH",atribute_url,HTTP.entities_headers,json.dumps(listofchanges))

		#Update the current state of the entity
		self.get()

	#The function exists verifies if the self.id is already present in the broker
	def exists(self):
		entity_url = HTTP.entities_url + "/" + self.id + "/?options=keyValues&attrs=type"
		
		#Simple get of the entity, if the response is empty the entity don't exist in the broker
		response = HTTP.sendRequest("GET",entity_url,HTTP.headers_get_iot)
		
		if self.id in response:
				return True
		return False

	#The delete function deletes the entity from the broker 
	def delete(self):
		entity_url = HTTP.entities_url + "/" + self.id
		HTTP.sendRequest("DELETE",entity_url)

	def toString(self):
		return json.dumps(self.json_entity,indent=2)

class Worker(Entity):
	def __init__(self,id=Null, name=Null, rfidCode=Null, description=Null):
		super().__init__(type="Worker",id=id,name=name,description=description)
		self.addAttr("rfidCode","Text",rfidCode)
		self.entity_rfidCode = rfidCode

	def getRFIDCode(self):
		return self.entity_rfidCode

	#Get the worker information form the broker through the respective rfidCode
	def getByRFIDCode(self, rfidCode):
		entity_url = HTTP.entities_url + "/?type=Worker&q=rfidCode=='" +rfidCode+ "'&options=keyValues&attrs=." 

		response = HTTP.sendRequest("GET",entity_url,HTTP.headers_get_iot)
		json_response = json.loads(response)

		if len(json_response) > 0:
			if "id" in json_response[0]:
				worker_ref = json_response[0]["id"]
				self.get(worker_ref)
				return True

		return False

	def toString(self):
		return "Worker: " + str(self.id) + " - " + self.entity_rfidCode

class Station(Entity):
	def __init__(self,id=Null,name=Null, description=Null, refPrevious=Null, refFollowing=Null, refScript=Null):
			super().__init__(type="Station",id=id,name=name,description=description)
			self.addAttr("refPrevious","Relationship",refPrevious)
			self.addAttr("refFollowing","Relationship",refFollowing)
			self.addAttr("refScript","Relationship",refScript)
			self.addAttr("CO2","Float","0.0")
			self.addAttr("humidity","Float","0.0")
			self.addAttr("luminosity","Float","0.0")
			self.addAttr("productivity","Float","0.0")
			self.addAttr("temperature","Float","0.0")

	def gePrevious(self): 
		if "refPrevious" in self.json_entity:
			if "value" in self.json_entity["refPrevious"]:
				previousStation = Station()
				previousStation.get(self.json_entity["refPrevious"]["value"])
				return previousStation
		return None

	def getFollowing(self):
		if "refFollowing" in self.json_entity:
			if "value" in self.json_entity["refFollowing"]:
				nextStation = Station()
				nextStation.get(self.json_entity["refFollowing"]["value"])
				return nextStation
		return None

	def getScript(self):
		if "refScript" in self.json_entity:
			if "value" in self.json_entity["refScript"]:
				script = Script()
				script.get(self.json_entity["refScript"]["value"])
				return script
		return None

class Script(Entity):
	def __init__(self,id=Null,name=Null, refStation=Null, refFirst=Null, description=Null):
			super().__init__(type="Script",id=id,name=name,description=description)
			self.addAttr("refStation","Relationship",refStation)
			self.addAttr("refFirstTask","Relationship",refFirst)
			self.addAttr("refCurrentTask","Relationship","") 
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
		url = HTTP.entities_url + "/?q=refStation=='" + refStation + "'&type=Script&options=keyValues&attrs=type"
		response = json.loads(HTTP.sendRequest("GET",url, HTTP.headers_get_iot))

		#The response contains only one entity
		#	the entity contains the id and type
		if len(response)==1 and len(response[0])==2:
			self.get(response[0]["id"])
			return True
			
		return False

	def getFistTask(self):
		if "refFirstTask" in self.json_entity:
			if "value" in self.json_entity["refFirstTask"]:
				firstTask = Task()
				firstTask.get(self.json_entity["refFirstTask"]["value"])
				return firstTask
		return None

	def getCurrentlTask(self):
		if "refCurrentTask" in self.json_entity:
			if "value" in self.json_entity["refCurrentTask"]:
				newtask = Task()
				newtask.get(self.json_entity["refCurrentTask"]["value"])
				return newtask
		return None

	#def getWorker(self):
	#	worker = Worker()
	#	worker.get(self.json_entity["refWorker"]["value"])
	#	return worker

	#Get the current number of Tasks
	def getNumTasks(self):
		url = HTTP.entities_url + "/?type=Task&q=refScript==\'" + self.id + "\'&attrs=type&options=values"

		response = HTTP.sendRequest("GET",url,HTTP.headers_get_iot)

		number_of_tasks = len(json.loads(response))
		return number_of_tasks

	#Update related to the state of the Script
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

		return processState

	#Updates related to the start point of the Script
	def initScript(self, timeInstant=Null):

		print(colored("\nInit Script"), "green")

		firstTask = self.getFistTask()
		firstTask_ref = firstTask.json_entity["id"]

		new_values = {}
		new_values["refCurrentTask"] = firstTask_ref
		new_values["taskNumber"] = "1"
		new_values["taskProcessState"] = self.updateProcessState(1)
		if timeInstant != Null:
			new_values["startTime"] = timeInstant
			new_values["stopTime"] = timeInstant

		self.update(new_values)

	#Updates related to the start point of the next Task
	def nextTask(self, timeInstant):
		actual = self.getCurrentlTask()
		next = actual.getNextTask()
		next_ref = next.json_entity["id"]

		new_values = {}

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

			self.initScript(timeInstant)
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

		new_values["refCurrentTask"] = next_ref
		new_values["taskNumber"] = str(nextTaskNum)
		new_values["taskProcessState"] = self.updateProcessState(nextTaskNum,"now")
		new_values["actualProcessState"] = str(format(actualProcessState, '.3f'))

		self.update(new_values)

class Task(Entity):
	def __init__(self,id=Null,name=Null, refScript=Null, refNextTask=Null, refRequirements=Null, description=Null):
			super().__init__(type="Task",id=id,name=name,description=description)
			self.addAttr("assemblyTime","Float","0.0")
			self.addAttr("startTime","DataTime","")
			self.addAttr("stopTime","DataTime","")
			self.addAttr("refScript","Relationship",refScript)
			self.addAttr("refRequirements","Relationship",refRequirements)
			self.addAttr("refNextTask","Relationship",refNextTask)

	def getScript(self):
		if "refScript" in self.json_entity:
			if "value" in self.json_entity["refScript"]:
				newScript = Script()
				newScript.get(self.json_entity["refScript"]["value"])
				return newScript
		return None

	def getRequirements(self):
		if "refRequirements" in self.json_entity:
			if "value" in self.json_entity["refRequirements"]:
				newRequirement = Requirements()
				newRequirement.get(self.json_entity["refRequirements"]["value"])
				return newRequirement
		return None

	def getNextTask(self):
		if "refNextTask" in self.json_entity:
			if "value" in self.json_entity["refNextTask"]:
				newtask = Task()
				newtask.get(self.json_entity["refNextTask"]["value"])
				return newtask
		return None

class Requirements(Entity):
	def __init__(self,id=Null,name=Null, query=Null, refSensor=Null, refStation=Null, max=Null, min=Null, description=Null):
		super().__init__(type="Requirements",id=id,name=name,description=description)
		self.addAttr("refDevice","Relationship",refSensors)
		self.addAttr("refStation", "Relationship", refDevice)
		self.addAttr("query", "Query", query)
		self.addAttr("max", "Float", max)
		self.addAttr("min", "Float", min)

	def getDevice(self):
		if "refDevice" in self.json_entity:
			if "value" in self.json_entity["refDevice"]:
				device = Device()
				device.get(self.json_entity["refDevice"]["value"])
				return device
		return None

	def getStation(self):
		if "refStation" in self.json_entity:
			if "value" in self.json_entity["refStation"]:
				station = Station()
				station.get(self.json_entity["refStation"]["value"])
				return station
		return None

class Device(Entity):
	def __init__(self):
		super().__init__(type="Device")

	def __init__(self,id=Null,name=Null, description=Null):
		super().__init__(type="Device",id=id,name=name,description=description)

	def get(self, entity_id):
		self.id = entity_id
		entity_url = HTTP.entities_url + "/" + self.id

		response = HTTP.sendRequest("GET",entity_url,HTTP.headers_get_iot)
		self.json_entity = json.loads(response)

	def getByStation(self, refStation):
		url = HTTP.entities_url + "/?q=refStation=='" + refStation + "'&type=Led&options=keyValues&attrs=type&limit=1"
		response = json.loads(HTTP.sendRequest("GET",url, HTTP.headers_get_iot))

		print("GET LED: " + json.dumps(response))

		if len(response)==1 and len(response[0])==2:
			self.get(response[0]["id"])
			return True
			
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
					HTTP.sendRequest("PATCH",HTTP.entities_url + "/" + self.json_entity["id"] + "/attrs",HTTP.iot_headers,json.dumps(payload))
					return True

		print(colored("Error, the command could not be sent: ", "red") + command)
		return False
