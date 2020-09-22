import json
from termcolor import colored
from datetime import datetime

from . import HTTPCommands as HTTP

import Classes.DB_Entities as DB_Entities

Null = "Null"
DateTimeFormat = "%Y-%m-%d %H:%M:%S.%f%z"

def getWorkCenters():
	query = HTTP.entities_url + "/?type=WorkCenter&options=keyValues&attrs=id&limit=1000"

	response,headers = HTTP.sendRequest("GET",query,HTTP.headers_get_iot)

	json_entity = {}
	if response != None:
		json_entity = json.loads(response)

	string = None
	if len(json_entity)>0:
		string = "("

		for w in json_entity:
			string = string + "'" + w["id"][23:] + "', "

		string = string[:-2] + ")"

	return string

def getParts():
	query = HTTP.entities_url + "/?type=Part&options=keyValues&attrs=id&limit=1000"

	response,headers = HTTP.sendRequest("GET",query,HTTP.headers_get_iot)

	json_entity = {}
	if response != None:
		json_entity = json.loads(response)

	string = None
	if len(json_entity)>0:
		string = "("

		for p in json_entity:
			string = string + "'" + p["id"][17:] + "', "

		string = string[:-2] + ")"

	return string

#Ao contrário das restantes entidades, as orders podem superar o limite de 1000 entidades com facilidade ...
#Para contornar isso, os pedidos são repetidos consoante o número de entidades que satisfazem os critérios da query ...
def getRunningOrders():
	query = HTTP.entities_url + "/?q=orderNewStatus!='COMPLETE';orderNewStatus!='CANCELLED'&type=Order&options=keyValues,count&attrs=id,orderNumber,statusChangeTS&limit=100"

	numberOfEntities = 1
	json_entity = {}
	orderList = {}
	offSet="0"

	while len(orderList) < numberOfEntities:
		#O offset determina o ponto de partida de onde os elementos devem se considerados ...
		offSet = str(len(orderList))

		response, headers = HTTP.sendRequest("GET",query + "&offset=" + offSet,HTTP.headers_get_iot)

		if "Fiware-Total-Count" in headers:
			numberOfEntities=int(headers["Fiware-Total-Count"])

		if response != None:
			json_entity = json.loads(response)

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
	query = HTTP.entities_url + "/?q=operationNewStatus!='COMPLETE';operationNewStatus!='CANCELLED'&type=Operation&options=keyValues,count&limit=100"

	numberOfEntities = 1
	numberOfOperations = 0
	json_entity = {}
	operationList = {}
	offSet="0"

	while numberOfOperations < numberOfEntities:
		#O offset determina o ponto de partida de onde os elementos devem se considerados ...
		offSet = str(numberOfOperations)

		response,headers = HTTP.sendRequest("GET",query + "&offset=" + offSet,HTTP.headers_get_iot)

		if "Fiware-Total-Count" in headers:
			numberOfEntities=int(headers["Fiware-Total-Count"])

		if response != None:
			json_entity = json.loads(response)

		for o in json_entity:
			operation = Operation()
			operation.loadJsonEntity(o)
			orderNumber = operation.getOrderNumber()
			operationNumber = operation.getOperationID()

			if not orderNumber in operationList:
				operationList.update({orderNumber: {}})

			if not (operationNumber in operationList[orderNumber]) or operation.compareTimeStams(operationList[orderNumber][operationNumber]):
				operationList[orderNumber].update({operationNumber: (operation)})
				numberOfOperations = numberOfOperations + 1

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

#The delete function deletes the entity from the broker 
def deleteEntity(entity_id):
	entity_url = HTTP.entities_url + "/" + entity_id
	HTTP.sendRequest("DELETE",entity_url)

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
		print(self.json_entity)
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

		response,headers = HTTP.sendRequest("GET",url_services,HTTP.iot_headers,json.dumps(payload_service))
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

		response,headers = HTTP.sendRequest("GET",url_services,HTTP.iot_headers,json.dumps(payload_service))
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

	#The addAttr function adds a new attribute to the Entity ??? type ...
	def setAttr(self, name, value, type="Text"):
		if not(name in self.json_entity):
			self.addAttr(name,type,value)
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

	def removeAttr(self, attr):
		return self.json_entity.pop(attr, None)

	def removeListAttr(self, attrList):
		for l in attrList:
			self.json_entity.pop(l, None)

	#The get function will copy the data hold by the broker and load the Entity
	def get(self, entity_id=Null, query=Null):
		if entity_id != Null:
			self.id = entity_id
			entity_url = HTTP.entities_url + "/" + self.id
		else:
			if query != Null:
				entity_url = HTTP.entities_url + "/?"
				entity_url = entity_url + query
			else:
				return False

		response,headers = HTTP.sendRequest("GET",entity_url,HTTP.headers_get_iot)

		response_json = json.loads(response)

		print(response_json)

		if len(response_json)>0 and 0 in response_json and "type" in response_json[0]:
			self.load(response_json[0])
			return True
		else:
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

		# POST can "create" new attrs ... for now the patch is sufficient ... ???
		HTTP.sendRequest("POST",atribute_url,HTTP.entities_headers,json.dumps(newValues))

	def updateAttr(self, attr):
		newValues={}

		if attr in self.json_entity:
			if isinstance(self.json_entity[attr],dict):
				newValues[attr] = self.json_entity[attr]["value"]
			else:
				newValues[attr] = self.json_entity[attr]

		entity_url = HTTP.entities_url + "/" + self.id
		atribute_url = entity_url + "/attrs/?options=keyValues"

		# POST can "create" new attrs ... for now the patch is sufficient ... ???
		HTTP.sendRequest("POST",atribute_url,HTTP.entities_headers,json.dumps(newValues))

	def updateAttrList(self, attrList):
		newValues={}

		for attr in attrList:
			if attr in self.json_entity:
				if isinstance(self.json_entity[attr],dict):
					newValues[attr] = self.json_entity[attr]["value"]
				else:
					newValues[attr] = self.json_entity[attr]

		entity_url = HTTP.entities_url + "/" + self.id
		atribute_url = entity_url + "/attrs/?options=keyValues"

		print(attrList,newValues)

		# POST can "create" new attrs ... for now the patch is sufficient ... ???
		HTTP.sendRequest("POST",atribute_url,HTTP.entities_headers,json.dumps(newValues))

	#The function exists verifies if the self.id is already present in the broker
	def exists(self):
		entity_url = HTTP.entities_url + "/" + self.id + "/?options=keyValues&attrs=type"
		
		#Simple get of the entity, if the response is empty the entity don't exist in the broker
		response,headers = HTTP.sendRequest("GET",entity_url,HTTP.headers_get_iot)
		
		if response != None and self.id in response:
				return True
		return False

	#The delete function deletes the entity from the broker 
	def delete(self):
		entity_url = HTTP.entities_url + "/" + self.id
		HTTP.sendRequest("DELETE",entity_url)

	def __eq__(self, other): 
		if not isinstance(other, Entity):
			return NotImplemented

		if  other.getJson() == None:
			return False

		if other.getID() == None or (self.getID() == None or (self.getID()!= other.getID())):
			return False

		if other.getType() == None or (self.getType() == None or (self.getType()!= other.getType())):
			return False

		for key in self.json_entity:
			if other.getAttrValue(key) != None and self.getAttrValue(key) !=  other.getAttrValue(key):
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

		response,headers = HTTP.sendRequest("GET",entity_url,HTTP.headers_get_iot)
		json_response = json.loads(response)

		if len(json_response) > 0:
			if "id" in json_response[0]:
				worker_ref = json_response[0]["id"]
				self.get(worker_ref)
				return True

		return False

	def __str__(self):
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
		self.addAttr("partNumber","Text",row["partnumber"])
		self.addAttr("site","Text",row["site"])
		self.addAttr("planedHours","Number",row["planedhours"])
		if row["scheduledstart"] == None:
			self.addAttr("scheduledStart","Number",0)
		else:
			scheduledStart = datetime.strptime(row["scheduledstart"], '%Y-%m-%d %H:%M:%S%z')
			self.addAttr("scheduledStart","Number",scheduledStart.timestamp())

		if row["scheduledend"] == None:
			self.addAttr("scheduledEnd","Number",0)
		else:
			scheduledEnd = datetime.strptime(row["scheduledend"], '%Y-%m-%d %H:%M:%S%z')
			self.addAttr("scheduledEnd","Number",scheduledEnd.timestamp())
		if row["actualstart"] == None:
			self.addAttr("actualStart","Number",0)
		else:
			actualStart = datetime.strptime(row["actualstart"], '%Y/%m/%d %H:%M:%S')
			self.addAttr("actualStart","Number",actualStart.timestamp())
		if row["actualend"] == None:
			self.addAttr("actualEnd","Number",0)
		else:
			actualend = datetime.strptime(row["actualend"], '%Y-%m-%d %H:%M:%S.%f%z')
			self.addAttr("actualEnd","Number",actualend.timestamp())
		self.addAttr("orderNewStatus","Text",row["ordernewstatus"])
		self.addAttr("orderOldStatus","Text",row["orderoldstatus"])
		statusChangeTS = datetime.strptime(row["statuschangets"], '%Y-%m-%d %H:%M:%S%z')
		self.addAttr("statusChangeTS","Number",statusChangeTS.timestamp())
		self.addAttr("totalPlanedHours","Number",float(row["totalplanedhours"]))

		#Os pedidos a Base de Dados devem ser minimizados na fase de alocação dos dados ???
		totalActualHours = DB_Entities.readTotalActualHours(self.getAttrValue("orderNumber"))
		if totalActualHours == None:
			totalActualHours = 0

		self.addAttr("totalActualHours","Number",float(totalActualHours))
		self.addAttr("totalNumberOfOperations","Integer",int(row["totalnumberofoperations"]))

		#Os pedidos a Base de Dados devem ser minimizados na fase de alocação dos dados ???
		totalNumberOfEndedOperations = DB_Entities.readNumberOfEndedOperations(self.getAttrValue("orderNumber"))
		if totalNumberOfEndedOperations == None:
			totalNumberOfEndedOperations = 0

		self.addAttr("totalNumberOfEndedOperations","Integer",int(totalNumberOfEndedOperations))

		self.addAttr("scheduledDelay","Text","-")
		self.addAttr("progressDelay","Text","-")

	def processDelay(self):
		self.processScheduleDelay()
		self.processProgressDelay()

		attrList = ["scheduledDelay","progress","progressDelay"]
		self.updateAttrList(attrList)

	def processScheduleDelay(self):

		if self.json_entity["orderNewStatus"] == "RUN":
			scheduledStart = self.getAttrValue("scheduledStart")

			if scheduledStart != None and scheduledStart != 0:

				now = datetime.now().timestamp()

				if now > (scheduledStart + 21600):
					self.setAttr("scheduledDelay","Delayed start")
				else:
					if now < (scheduledStart - 21600):
						self.setAttr("scheduledDelay","Advanced start")
					else:
						self.setAttr("scheduledDelay","Normal start")
			else:
				self.setAttr("scheduledDelay","Indeterminate")
		else:
			if self.getAttrValue("scheduledDelay") == "-":
				self.setAttr("scheduledDelay","Indeterminate")

	def processProgressDelay(self):
		#All the operation already completed that are related to the order ...
		entity_url = HTTP.entities_url + "/?q=order_id=='" + self.getAttrValue("id")[18:] + "';operationStatus=='COMPLETED'&type=Operation&attrs=planedHours,actualHours&options=keyValues" 

		response,headers = HTTP.sendRequest("GET",entity_url,HTTP.headers_get_iot)

		totalPlanedHours = self.getAttrValue("totalPlanedHours")
		totalActualHours = self.getAttrValue("totalActualHours")

		#Compare expected time with actual time until now/ time spent in any completed operation until now ... 
		#ADVANCED(<-5%), NORMAL(+/- 5%) and DELAYED(>+5%) are the 3 states of delay
		if totalActualHours < totalPlanedHours*0.95:
			self.setAttr("progressDelay","ADVANCED")
		else:
			if totalActualHours > totalPlanedHours*0.95 and totalActualHours < totalPlanedHours*1.05:
				self.setAttr("progressDelay","NORMAL")
			else:
				self.setAttr("progressDelay","DELAYED")

		progress = None

		if totalActualHours>0 and totalPlanedHours>0:
			progress = int((totalActualHours/totalPlanedHours)*100)

		if progress != None:
			self.setAttr("progress",progress)
		else:
			self.setAttr("progress",0)

	def processOperationProcess(self, op, _progress):
		self.setAttr("currentOperation",op.getOperationNumber())

		op_planed_hours = op.getAttrValue("planedHours")

		totalPlanedHours = self.getAttrValue("totalPlanedHours")
		totalActualHours = self.getAttrValue("totalActualHours") + float(int(_progress)/100)*op_planed_hours

		progress = None

		if totalActualHours>0 or self.getAttrValue("orderNewStatus") == "RUN":
			progress = int((totalActualHours/totalPlanedHours)*100)

		if progress != None:
			self.setAttr("progress",progress)

		attrList = ["currentOperation","progress"]
		self.updateAttrList(attrList)

	def compareTimeStams(self, other):
		if self.getTimeStamp() > other.getTimeStamp():
			return True
		else:
			return False

	#The delete function deletes the entity from the broker 
	def deleteAll(self):
		super().delete()

		query = HTTP.entities_url + "/?q=order_id!='" + self.getOrderID() + "'&type=Operation&options=keyValues&attrs=id&limit=1000"

		response,headers = HTTP.sendRequest("GET",query,HTTP.headers_get_iot)

		json_entity = {}
		if response != None:
			json_entity = json.loads(response)

		# ??? Pode ser otimizado, só é necessário adequirir o ID ...
		for o in json_entity:
			deleteEntity(o["id"])

	def __eq__(self, other): 
		if not isinstance(other, Order):
			return NotImplemented

		return super().__eq__(other)

class WorkCenter(Entity):
	def __init__(self,row):
		super().__init__(type="WorkCenter",id=int(row["id"]),name="WorkCenter",description=row["denomination"])
		self.part_id = row["id"]
		self.payload = row

	def __eq__(self, other): 
		if not isinstance(other, WorkCenter):
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

	def getOrderID(self):
		return self.getAttrValue("orderNumber")

	def getTimeStamp(self):
		return self.getAttrValue("statusChangeTS")

	def loadDBEntry(self, row):
		super().__init__(type="Operation",id=str(row["ordernumber"])+str(row["operationnumber"]),name="Operation",description=row["description"])
		self.addAttr("workCenter_id","Text",str(row["workcenter_id"]))
		self.addAttr("order_id","Text",str(row["order_id"]))
		self.addAttr("operationNumber","Text",str(row["operationnumber"]))
		self.addAttr("planedHours","Number",row["planedhours"])
		self.addAttr("actualHours","Number",row["actualhours"])
		self.addAttr("operationNewStatus","Text",row["operationnewstatus"])
		self.addAttr("operationOldStatus","Text",row["operationoldstatus"])
		self.addAttr("statusChangeTS","Text",row["statuschangets"])
		self.addAttr("orderNumber","Text",row["ordernumber"])
		self.addAttr("progress","Text","-")

	def compareTimeStams(self, other):
		if self.getTimeStamp() > other.getTimeStamp():
			return True
		else:
			return False

	#GET the WC associated to this operation
	#def getWorkCenter(self):
	#	if "refWorkCenter" in self.json_entity:
	#		if "value" in self.json_entity["refWorkCenter"]:
	#			newStation = Station()
	#			newStation.get(self.json_entity["refWorkCenter"]["value"])
	#			return newStation
	#	return None

	def processProgress(self, progress):
		self.setAttr("progress","Text",str(progress))
		self.updateAttr("progress")

class Part(Entity):
	def __init__(self,row):
		super().__init__(type="Part",id=int(row["id"]),name="Part",description=row["description"])
		self.part_id = row["id"]
		self.addAttr("partNumber","Text",row["partnumber"])
		self.addAttr("serialNumber","Text",row["serialnumber"])
		self.addAttr("partRev","Text",row["partrev"])
		self.addAttr("cemb","Text",row["cemb"])
		self.addAttr("planedHours","Number",row["planedhours"])

	def getID(self):
		return self.part_id

	def getByOperation(self, refOperation):
		return False

	def __eq__(self, other): 
		if not isinstance(other, Part):
			return NotImplemented

		return self.json_entity == other.json_entity


#class Requirements(Entity):
#	def __init__(self,id=Null,name=Null, query=Null, refSensor=Null, refStation=Null, max=Null, min=Null, description=Null):
#		super().__init__(type="Requirements",id=id,name=name,description=description)
#		self.addAttr("refDevice","Relationship",refSensors)
#		self.addAttr("refStation", "Relationship", refDevice)
#		self.addAttr("query", "Query", query)
#		self.addAttr("max", "Number", max)
#		self.addAttr("min", "Number", min)
#
#	def getDevice(self):
#		if "refDevice" in self.json_entity:
#			if "value" in self.json_entity["refDevice"]:
#				device = Device()
#				device.get(self.json_entity["refDevice"]["value"])
#				return device
#		return None
#
#	def getStation(self):
#		if "refStation" in self.json_entity:
#			if "value" in self.json_entity["refStation"]:
#				station = Station()
#				station.get(self.json_entity["refStation"]["value"])
#				return station
#		return None
#
#class Device(Entity):
#	def __init__(self):
#		super().__init__(type="Device")
#
#	def __init__(self,id=Null,name=Null, description=Null):
#		super().__init__(type="Device",id=id,name=name,description=description)
#
#	def get(self, entity_id):
#		self.id = entity_id
#		entity_url = HTTP.entities_url + "/" + self.id
#
#		response,headers = HTTP.sendRequest("GET",entity_url,HTTP.headers_get_iot)
#		self.json_entity = json.loads(response)
#
#	def getByStation(self, refStation):
#		url = HTTP.entities_url + "/?q=refStation=='" + refStation + "'&type=Led&options=keyValues&attrs=type&limit=1"
#		response = json.loads(HTTP.sendRequest("GET",url, HTTP.headers_get_iot)[0])
#
#		if len(response)==1 and len(response[0])==2:
#			self.get(response[0]["id"])
#			return True
#			
#		return False
#
#	def execCommand(self, command):
#		if "id" in self.json_entity:
#			if command in self.json_entity:
#				if "Command" in self.json_entity[command].values():
#
#					payload = {}
#					payload[command] = {}
#					payload[command]["type"] = "Command"
#					payload[command]["value"] = ""
#
#					print(colored("Send command: ", "green") + command)
#					HTTP.sendRequest("PATCH",HTTP.entities_url + "/" + self.json_entity["id"] + "/attrs",HTTP.iot_headers,json.dumps(payload))
#					return True
#
#		print(colored("Error, the command could not be sent: ", "red") + command)
#		return False
