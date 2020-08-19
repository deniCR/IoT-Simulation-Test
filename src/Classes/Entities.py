import json
from time import sleep
from termcolor import colored
from datetime import datetime, timedelta

from . import HTTPCommands as HTTP

import Classes.DB_Entities as DB_Entities

import psycopg2

Null = "Null"
DateTimeFormat = "%Y-%m-%dT%H:%M:%S.00Z"
Null_Time = datetime.strptime("1900-01-01T12:00:00.00Z", DateTimeFormat)

#Leitura a partir de um ficheiro de configuração...
conn = psycopg2.connect("dbname=MES-DB user=postgres host=192.168.2.108 port=5432")

def getRunningOrders():
	query = HTTP.entities_url + "/?q=orderNewStatus!='COMPLETE';orderNewStatus!='CANCELLED'&type=Order&options=keyValues&attrs=id,orderNumber,statusChangeTS&limit=1000"

	response = HTTP.sendRequest("GET",query,HTTP.headers_get_iot)

	json_entity = {}
	if response != None:
		json_entity = json.loads(response)

	orderList = {}
	for o in json_entity:
		order = Order()
		order.loadJsonEntity(o)
		orderList.update({order.getOrderID(): (order)})

	string = None

	if len(orderList) > 0:
		string = "("

		for o in orderList:
			string = string + "'" + o + "', "

		string = string[:-2] + ")"

	return orderList,string

#Pode não ser necessário colletar todas as operações ... Pode ser feito para cada order ... ???
def getRunningOperations():
	query = HTTP.entities_url + "/?q=operationNewStatus!='COMPLETE';operationNewStatus!='CANCELLED'&type=Operation&options=keyValues&limit=1000"

	response = HTTP.sendRequest("GET",query,HTTP.headers_get_iot)

	json_entity = {}
	if response != None:
		json_entity = json.loads(response)

	operationList = {}
	for o in json_entity:
		operation = Operation()
		operation.loadJsonEntity(o)
		orderNumber = operation.getOrderNumber()
		operationNumber = operation.getOperationID()

		if not orderNumber in operationList:
			operationList.update({orderNumber: {}})

		if not (operationNumber in operationList[orderNumber]) or operation.getTimeStamp() > operationList[orderNumber][operationNumber].getTimeStamp():
			operationList[orderNumber].update({operationNumber: (operation)})

	strings = {}

	if len(operationList) > 0:
		for orderN in operationList:
			string = None
			if len(operationList[orderN]) > 0:
				string = "("
				for o in operationList[orderN].values():
					string = string + "'" + o.getOperationNumber() + "', "

				string = string[:-2] + ")"
			strings.update({orderN: string})

	return operationList,strings


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

	def __str__(self):
		return ("Entity(ID: " + str(self.getID()) + ")")

	def getJson(self):
		return self.json_entity

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
		value = None
		if attr in self.json_entity:
			if isinstance(self.json_entity[attr],dict) and "value" in self.json_entity[attr]:
				value = self.json_entity[attr]["value"]
			else:
				value = self.json_entity[attr]
		return value

	#The load function will load all the information from the json object
	def load(self, entity):

		if isinstance(entity,dict):
			json_entity = entity
		else:
			json_entity = json.loads(entity)

		if "id" in json_entity:
			self.id = json_entity["id"]
		if "type" in json_entity:
			self.type = json_entity["type"]

		self.json_entity = json_entity

	#The addAttr function adds a new attribute to the Entity
	def updateAttr(self, name, value):
		if not(name in self.json_entity):
			self.addAttr(name,"Text",value)
		else:
			if isinstance(self.json_entity[name],dict) and "value" in self.json_entity[name]:
				self.json_entity[name]["value"]=value
			else:
				self.json_entity[name]=value #??? Caso em que o json só tem keyValue atributos ...

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
			return 1
		else:
			print(colored("Warning - (Duplicate): ","red"),"The entity: " + str(self) + " already exists in the broker ...")
			return 0

	#def updateValue(self,attribute,new_value):

	def update(self):
		newValues={}

		for attr, value in self.json_entity.items():
			if isinstance(value,dict):
				newValues[attr] = value["value"]
			else:
				if attr != "id" and attr != "type":  #??? Values with and without the parameters type, and meta-data ...
					newValues[attr] = value

		entity_url = HTTP.entities_url + "/" + self.id
		atribute_url = entity_url + "/attrs/?options=keyValues"

		print("Update id: " + entity_url)
		print(json.dumps(newValues))

		# PUT can "create" new attrs ... for now the patch is sufficient ... ???
		HTTP.sendRequest("PATCH",atribute_url,HTTP.entities_headers,json.dumps(newValues))

#	#Updates one (doesn't append new attributes)
#	def update(self,listofchanges):
#		deleteAttrs = []
#
#		#Change the values of the respective keys ...
#		for key in listofchanges:
#			if key in self.json_entity:
#				self.json_entity[key] = listofchanges[key]
#			else:
#				deleteAttrs.append(key)
#
#		#Delete the attributes that aren't present in the object
#		for key in deleteAttrs:
#			del listofchanges[key]
#
#		#Update only the values that correspond to the current attributes
#		if len(listofchanges) > 0:
#			entity_url = HTTP.entities_url + "/" + self.id
#			atribute_url = entity_url + "/attrs/?options=keyValues"
#
#			HTTP.sendRequest("PATCH",atribute_url,HTTP.entities_headers,json.dumps(listofchanges))
#
#		#Update the current state of the entity
#		self.get()

	#The function exists verifies if the self.id is already present in the broker
	def exists(self):
		entity_url = HTTP.entities_url + "/" + self.id + "/?options=keyValues&attrs=type"
		
		#Simple get of the entity, if the response is empty the entity don't exist in the broker
		response = HTTP.sendRequest("GET",entity_url,HTTP.headers_get_iot)
		
		if response != None and self.id in response:
				return True
		return False

	#The delete function deletes the entity from the broker 
	def delete(self):
		entity_url = HTTP.entities_url + "/" + self.id
		HTTP.sendRequest("DELETE",entity_url)

	def toString(self):
		return json.dumps(self.json_entity,indent=2)

	def __eq__(self, other): 
		if not isinstance(other, Entity):
			# don't attempt to compare against unrelated types
			return NotImplemented

		if  other.getJson() == None:
			return False

		if other.getID() == None or (self.getID() == None or (self.getID()!= other.getID())):
			return False

		if other.getType() == None or (self.getType() == None or (self.getType()!= other.getType())):
			return False

		for key in self.json_entity:
			if other.getAttrValue(key) != None and self.getAttrValue(key) !=  other.getAttrValue(key):
				print("Key: " + key)
				print("Different values- self: " + str(self.getAttrValue(key)) + " and other: " + str(other.getAttrValue(key)) + "\n")
				return False

		return True

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

class Order(Entity):
	def __init__(self,id=Null,name=Null,description=Null):
		super().__init__(type="Order",id=id,name=name,description=description)

	def __str__(self):
		return ("Order(Number: " + self.getOrderNumber() + ")")

	def loadJsonEntity(self, entity):
		super().load(entity)

	def getOrderID(self):
		return self.id[18:]

	def getOrderNumber(self):
		return self.getAttrValue("orderNumber")

	def getTimeStamp(self):
		return self.getAttrValue("statusChangeTS")

	def loadDBEntry(self, row):
		super().__init__(type="Order",id=str(row["ordernumber"]),name="Order",description=Null)
		self.addAttr("order_id","Text",row["id"])
		self.addAttr("orderNumber","Text",str(row["ordernumber"]))
		#self.addAttr("category","Text","???")
		self.addAttr("partNumber","Text",row["partnumber"])
		#self.addAttr("numberOfOperations","Integer",row["numberofoperations"])
		self.addAttr("site","Text",row["site"])
		self.addAttr("currentOperation","Text","-")
		self.addAttr("planedHours","Number",row["planedhours"])
		if row["scheduledstart"] == None:
			self.addAttr("scheduledStart","Text","-")
		else:
			self.addAttr("scheduledStart","Text",row["scheduledstart"])

		if row["scheduledend"] == None:
			self.addAttr("scheduledEnd","Text","-")
		else:
			self.addAttr("scheduledEnd","Text",row["scheduledend"])
		self.addAttr("actualStart","Text",row["actualstart"])
		self.addAttr("actualEnd","Text","-")
		self.addAttr("orderNewStatus","Text",row["ordernewstatus"])
		self.addAttr("orderOldStatus","Text",row["orderoldstatus"])
		self.addAttr("statusChangeTS","Text",row["statuschangets"])

		#if(row["actualhours"]!=None):
		#	self.addAttr("actualHours","Number",row["actualhours"])
		#else:
		#	self.addAttr("actualHours","Number",0)

		numberOfOperations = DB_Entities.readNumberOfTotalOperations(self.getAttrValue("orderNumber"))
		self.addAttr("numberOperations","Number",numberOfOperations)

		numberOfEndedOperations = DB_Entities.readNumberOfEndedOperations(self.getAttrValue("orderNumber"))
		self.addAttr("numberOfEndedOperations","Number",numberOfEndedOperations)

		self.addAttr("progress","Number","0")
		self.addAttr("scheduledDelay","Text","-")
		self.addAttr("progressDelay","Text","-")

	def updateProcessStatus(self):
		if self.getAttrValue("scheduledDelay") == "-":
			if date.today() > datetime.strptime(self.getAttrValue("scheduledDelay"), '%Y-%m-%d %H:%M:%S'):
				self.updateAttr("scheduledDelay","DELAYED")

		#estimate time until now

		#compare with real time (until now)...

	#def getPlanedHours(self):
	#	sum = 0
	#	with conn.cursor() as cur:
	#		cur.execute("""SELECT SUM(planedHours)
	#					FROM operation_status_changes
	#					WHERE order_id = %s; 
	#				""",(self.order_id,))
	#		sum = float(cur.fetchone()[0])
	#	return sum

	def processScheduleDelay(self):
		if self.json_entity["scheduledStart"] == "???" or self.json_entity["scheduledEnd"] == "???":
			self.updateAttr("scheduledDelay","Indeterminate")

		if self.json_entity["scheduledStart"] != None and self.json_entity["scheduledStart"] != "-":

			if self.getAttrValue("scheduledStart")!=None:
				scheduledStart = datetime.strptime(self.getAttrValue("scheduledStart"),'%Y-%m-%d %H:%M:%S')
			else:
				scheduledStart = now

			now = datetime.now()

			if now > (scheduledStart + timedelta(1)):
				self.updateAttr("scheduledDelay","Delayed start")
			else:
				self.updateAttr("scheduledDelay","Normal")
		else:
			self.updateAttr("scheduledDelay","???")

	def processProgressDelay(self):
		#All the operation already completed that are related to the order ...
		entity_url = HTTP.entities_url + "/?q=order_id=='" + self.getAttrValue("id")[18:] + "';operationStatus=='COMPLETED'&type=Operation&attrs=planedHours,actualHours&options=keyValues" 

		response = HTTP.sendRequest("GET",entity_url,HTTP.headers_get_iot)
		json_response = json.loads(response)

		#print(json_response)

		planedhours = 0
		actualhours = 0
		for op in json_response:
			if "planedHours" in op:
				planedhours = planedhours + op["planedHours"]
				actualhours = actualhours + op["actualHours"]

		# ??? Update the hours in the database ...
		#self.updateAttr("actualHours",actualhours)

		completedOperations = self.getAttrValue("numberOperations")
		ended_op = self.getAttrValue("numberOfEndedOperations")

		progress = 0
		if ended_op>0:
			progress = int((completedOperations/ended_op)*100)
		self.updateAttr("progress",progress)

		#Compare expected time with actual time until now/ time spent in any completed operation until now ... 
		#ADVANCED(<-5%), NORMAL(+/- 5%) and DELAYED(>+5%) are the 3 states of delay

		if actualhours < planedhours*0.95:
			self.updateAttr("progressDelay","ADVANCED")
		else:
			if actualhours > planedhours*0.95 and actualhours < planedhours*1.05:
				self.updateAttr("progressDelay","NORMAL")
			else:
				self.updateAttr("progressDelay","DELAYED")

	def compareTimeStams(self, other):
		if self.getTimeStamp() > other.getTimeStamp():
			return True
		else:
			return False


	def __eq__(self, other): 
		if not isinstance(other, Order):
			# don't attempt to compare against unrelated types
			return NotImplemented

		return super().__eq__(other)

#class Station(Entity):
	#def __init__(self,id=Null,name=Null, description=Null, refPrevious=Null, refFollowing=Null, refScript=Null):
			#super().__init__(type="Station",id=id,name=name,description=description)
			#self.addAttr("refPrevious","Relationship",refPrevious)
			#self.addAttr("refFollowing","Relationship",refFollowing)
			#self.addAttr("refScript","Relationship",refScript)
			#self.addAttr("CO2","Float","0.0")
			#self.addAttr("humidity","Float","0.0")
			#self.addAttr("luminosity","Float","0.0")
			#self.addAttr("productivity","Float","0.0")
			#self.addAttr("temperature","Float","0.0")

class WorkCenter(Entity):
	def __init__(self,row):
		super().__init__(type="WorkCenter",id=int(row["id"]),name="WorkCenter",description=row["denomination"])
		self.part_id = row["id"]
		self.payload = row

	def __eq__(self, other): 
		if not isinstance(other, MyClass):
			# don't attempt to compare against unrelated types
			return NotImplemented

		return self.payload == other.payload

class Operation(Entity):
	def __init__(self,id=Null,name=Null,description=Null):
		super().__init__(type="Operation",id=id,name=name,description=description)

	def __str__(self):
		return ("Operation(Number: " + str(self.getOperationNumber()) + ")")

	def loadJsonEntity(self, entity):
		super().load(entity)

	def getOperationID(self):
		return self.id[22:]

	def getOperationNumber(self):
		return self.getAttrValue("operationNumber")

	def getOrderNumber(self):
		return self.getAttrValue("orderNumber")

	def getTimeStamp(self):
		return self.getAttrValue("statusChangeTS")

	def loadDBEntry(self, row):
		super().__init__(type="Operation",id=str(row["operationnumber"])+str(row["ordernumber"]),name="Operation",description=row["description"])
		self.addAttr("workCenter_id","Text",str(row["workcenter_id"]))
		self.addAttr("order_id","Text",str(row["order_id"]))
		self.addAttr("operationNumber","Text",str(row["operationnumber"]))
		self.addAttr("planedHours","Number",row["planedhours"])
		self.addAttr("operationNewStatus","Text",row["operationnewstatus"])
		self.addAttr("operationOldStatus","Text",row["operationoldstatus"])
		self.addAttr("statusChangeTS","Text",row["statuschangets"])
		self.addAttr("orderNumber","Text",row["ordernumber"])
		#if row["fristrundate"] != None:
		#	self.addAttr("fristRunDate","Text",row["fristrundate"])
		#else:
		#	self.addAttr("fristRunDate","Text","-")
		#if row["completerundate"] != None:
		#	self.addAttr("completeDate","Text",row["completerundate"])
		#else:
		#	self.addAttr("completeDate","Text","-")

	#GET the WC associated to this operation
	def getWorkCenter(self):
		if "refWorkCenter" in self.json_entity:
			if "value" in self.json_entity["refWorkCenter"]:
				newStation = Station()
				newStation.get(self.json_entity["refWorkCenter"]["value"])
				return newStation
		return None

	#GET the requirements associated to this operation
	def getRequirements(self):
		if "refRequirements" in self.json_entity:
			if "value" in self.json_entity["refRequirements"]:
				newRequirement = Requirements()
				newRequirement.get(self.json_entity["refRequirements"]["value"])
				return newRequirement
		return None

class Part(Entity):
	def __init__(self,row):
		super().__init__(type="Part",id=int(row["id"]),name="Part",description=row["description"])
		self.part_id = row["id"]
		self.addAttr("partNumber","Text","???")
		self.addAttr("serialNumber","Text",row["serialnumber"])
		self.addAttr("partRev","Text",row["partrev"])
		self.addAttr("cemb","Text",row["cemb"])
		self.addAttr("planedHours","Number",row["planedhours"])

	def getID(self):
		return self.part_id

	def getByOperation(self, refOperation):
		return False

	def __eq__(self, other): 
		if not isinstance(other, MyClass):
			# don't attempt to compare against unrelated types
			return NotImplemented

		return self.json_entity == other.json_entity

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

		#print("GET LED: " + json.dumps(response))

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
