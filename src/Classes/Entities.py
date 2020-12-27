import json
from termcolor import colored
from datetime import datetime

from . import HTTPCommands as HTTP

Null = "Null"

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

def getEndedOperations():
	query = HTTP.entities_url + "/?q=operationNewStatus=='COMPLETE','CANCELLED'&type=Operation&options=keyValues,count&limit=100"

	numberOfEntities = 1
	numberOfOperations = 0
	json_entity = {}
	operationList = {}
	offSet="0"

	while numberOfOperations < numberOfEntities:
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
	def getEntity(self, entity_id=Null):
		if entity_id != Null:
			self.id = entity_id
			entity_url = HTTP.entities_url + "/" + self.id

		response,headers = HTTP.sendRequest("GET",entity_url,HTTP.headers_get_iot)

		response_json = json.loads(response)

		if len(response_json)>0 and 'error' not in response_json and 'id' in response_json:
			self.load(response_json)
			return True
		else:
			return False

	#The get function will copy the data hold by the broker and load the Entity
	def get(self, query=Null):
		if query != Null:
			entity_url = HTTP.entities_url + "/?"
			entity_url = entity_url + query
		else:
			return False

		response,headers = HTTP.sendRequest("GET",entity_url,HTTP.headers_get_iot)

		response_json = json.loads(response)

		print(response_json)

		if len(response_json)>0 and 'error' not in response_json and "id" in response_json[0]:
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

class Order(Entity):
	def __init__(self,id=Null,name=Null,description=Null):
		super().__init__(type="Order",id=id,name=name,description="description")

	def __str__(self):
		return ("Order(Number: " + self.getOrderNumber() + ")")

	def loadJsonEntity(self, entity):
		super().load(entity)

	def getOrderID(self):
		return self.id[18:]

	def getOrderNumber(self):
		return self.getAttrValue("orderNumber")

	def getTimestamp(self):
		return self.getAttrValue("statusChangeTS")

	def loadDBEntry(self, row):
		super().__init__(type="Order",id=str(row["ordernumber"]),name="Order",description="description")
		#self.addAttr("order_id","Text",row["id"])
		self.addAttr("orderNumber","Text",str(row["ordernumber"]))
		self.addAttr("partNumber","Text",row["partnumber"])
		self.addAttr("site","Text",row["site"])
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
		orderNewStatus = row["ordernewstatus"]
		self.addAttr("orderNewStatus","Text",orderNewStatus)
		self.addAttr("orderOldStatus","Text",row["orderoldstatus"])
		statusChangeTS = datetime.strptime(row["statuschangets"], '%Y-%m-%d %H:%M:%S%z')
		self.addAttr("statusChangeTS","Number",statusChangeTS.timestamp())

		totalHours = row["totalhours"]
		if totalHours == None:
			totalHours = 0
		totalHours = float(totalHours)
		self.addAttr("totalHours","Number",totalHours)

		plannedHours = float(row["plannedhours"])
		if plannedHours==0:
			plannedHours=totalHours
		self.addAttr("plannedHours","Number",plannedHours)

		currentHours = row["currenthours"]

		if orderNewStatus in ("COMPLETE","CANCELLED"): #Change in the Generator ...
			currentHours = totalHours
		if currentHours!=None:
			self.addAttr("currentHours","Number",float(currentHours))

		self.addAttr("scheduledDelay","Text","-")
		self.addAttr("progressDelay","Text","-")

		updateTS = datetime.strptime(row["updatets"], '%Y-%m-%d %H:%M:%S.%f%z')
		self.addAttr("updateTS","Number",updateTS.timestamp())

	def processDelay(self):
		self.processScheduleDelay()
		self.processProgressDelay()

		attrList = ["scheduledDelay","progressDelay","expectedProgress","actualProgress"]
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
		plannedHours = self.getAttrValue("plannedHours")
		currentHours = self.getAttrValue("currentHours")
		totalHours = self.getAttrValue("totalHours")

		if totalHours > 0:
			actualProgress = int(currentHours/totalHours*100)
		else:
			actualProgress = 0

		if plannedHours>0:
			expectedProgress = int(currentHours/plannedHours*100)
			if actualProgress > expectedProgress*1.05:
				self.setAttr(name="progressDelay",value="ADVANCED",type="Text")
			else:
				if actualProgress < expectedProgress*0.95:
					self.setAttr(name="progressDelay",value="DELAYED",type="Text")
				else:
					self.setAttr(name="progressDelay",value="NORMAL",type="Text")
		else:
			expectedProgress = 0
			self.setAttr(name="progressDelay",value="Indeterminate",type="Text")

		self.setAttr(name="expectedProgress",value=expectedProgress,type="Number")
		self.setAttr(name="actualProgress",value=actualProgress,type="Number")

	def processOperationProgress(self, op, _progress, ts):
		self.setAttr("currentOperation",op.getOperationNumber())

		op_planned_hours = float(op.getAttrValue("totalHours"))
		op_actual_hours = float(_progress*op_planned_hours/100)

		plannedHours = float(self.getAttrValue("plannedHours"))
		currentHours = float(self.getAttrValue("currentHours"))
		totalHours = float(self.getAttrValue("totalHours"))
		actualProgress = float(self.getAttrValue("actualProgress"))

		_currentHours = currentHours + op_actual_hours
		
		if totalHours > 0:
			_actualProgress = int(currentHours/totalHours*100)
		else:
			_actualProgress = 0
			_currentHours = 0

		#Cases that can occur with the aggregation of actualHours from the operations
		if actualProgress > _actualProgress or _actualProgress > 100:
			_actualProgress = actualProgress
			_currentHours = currentHours
		#else:
			#self.setAttr(name="currentHours",value=_currentHours,type="Number")

		expectedProgress = None

		if plannedHours<=0:
			expectedProgress=0
			self.setAttr(name="progressDelay",value="Indeterminate",type="Text")
		else:
			expectedProgress = int(_currentHours/plannedHours*100)
			if _actualProgress > (expectedProgress*1.05):
				self.setAttr(name="progressDelay",value="ADVANCED",type="Text")
			else:
				if _actualProgress < (expectedProgress*0.95):
					self.setAttr(name="progressDelay",value="DELAYED",type="Text")
				else:
					self.setAttr(name="progressDelay",value="NORMAL",type="Text")

		self.setAttr("expectedProgress",expectedProgress)
		self.setAttr(name="statusChangeTS",value=float(ts),type="Number")

		#Prevent possible superpositions of different operations updates ...
		if _actualProgress >= actualProgress:
			self.setAttr(name="actualProgress",value=_actualProgress,type="Number")

		if self.getAttrValue("scheduledDelay")=="-":
			self.processScheduleDelay()

		attrList = ["currentOperation","scheduledDelay","progressDelay","expectedProgress","actualProgress","currentHours","statusChangeTS"]
		self.updateAttrList(attrList)

	def compareTimeStams(self, other):
		if self.getTimestamp() > other.getTimestamp():
			return True
		else:
			return False

	#The delete function deletes the entity from the broker 
	def deleteAll(self):
		super().delete()

		query = HTTP.entities_url + "/?q=orderNumber=='" + self.getOrderID() + "'&type=Operation&options=keyValues&attrs=id&limit=1000"

		response,headers = HTTP.sendRequest("GET",query,HTTP.headers_get_iot)

		json_entity = {}
		if response != None:
			json_entity = json.loads(response)

		for o in json_entity:
			deleteEntity(o["id"])

	def __eq__(self, other): 
		if not isinstance(other, Order):
			return NotImplemented

		return super().__eq__(other)

class Operation(Entity):
	def __init__(self,id=Null,name=Null,description=Null):
		super().__init__(type="Operation",id=id,name=name,description="description")

	def __str__(self):
		return ("Operation(Number: " + str(self.getOperationNumber()) + ", Order: " + str(self.getOrderNumber()) + ")")

	def loadJsonEntity(self, entity):
		super().load(entity)

	def getOperationID(self):
		return (str(self.getAttrValue("orderNumber") + str(self.getAttrValue("operationNumber"))))

	def getOperationNumber(self):
		return self.getAttrValue("operationNumber")

	def getOrderNumber(self):
		return self.getAttrValue("orderNumber")

	def getOrderID(self):
		return self.getAttrValue("orderNumber")

	def getTimestamp(self):
		return self.getAttrValue("statusChangeTS")

	def loadDBEntry(self, row):
		super().__init__(type="Operation",id=str(row["ordernumber"])+str(row["operationnumber"]),name="Operation",description="description")
		self.addAttr("workCenter_id","Text",str(row["workcenter_id"]))
		#self.addAttr("order_id","Text",str(row["order_id"]))
		self.addAttr("operationNumber","Text",str(row["operationnumber"]))
		totalHours = float(row["totalhours"])
		self.addAttr("totalHours","Number",totalHours)
		plannedHours = float(row["plannedhours"])
		#Enable delay analysis ...
		if plannedHours == 0:
			plannedHours = totalHours
		self.addAttr("plannedHours","Number",plannedHours)
		actualHours = float(row["actualhours"])
		self.addAttr("actualHours","Number",actualHours)
		self.addAttr("operationNewStatus","Text",row["operationnewstatus"])
		self.addAttr("operationOldStatus","Text",row["operationoldstatus"])
		statusChangeTS = datetime.strptime(row["statuschangets"], '%Y-%m-%d %H:%M:%S%z')
		self.addAttr("statusChangeTS","Number",statusChangeTS.timestamp())
		self.addAttr("orderNumber","Text",row["ordernumber"])

		updateTS = datetime.strptime(row["updatets"], '%Y-%m-%d %H:%M:%S.%f%z')
		self.addAttr("updateTS","Number",updateTS.timestamp())

		expectedProgress = None
		actualProgress = None

		if row["operationnewstatus"]=="UNRELEASED":
			expectedProgress=0
		else:
			if row["operationnewstatus"] == "COMPLETE":
				actualProgress=100

		if row["actualprogress"]:
			actualProgress = int(row["actualprogress"])
		else:
			if not row["operationnewstatus"] in ("COMPLETE","CANCELLED"):
				if actualHours!=None and (totalHours!=None and totalHours>0):
					actualProgress = int(actualHours/totalHours*100)

		if expectedProgress==None and actualHours!=None and (plannedHours!=None and plannedHours>0):
			expectedProgress = int(actualHours/plannedHours*100)

		if expectedProgress!=None:
			self.addAttr("expectedProgress","Number",expectedProgress)
		else:
			expectedProgress=0
		if actualProgress!=None:
			self.addAttr("actualProgress","Number",actualProgress)
		else:
			actualProgress=0

		#The processDelay should be update in a similar way as the Order.progressDelay ...
		# through the delayAnalysis sub/not
		if plannedHours > 0:
			expectedProgress = int(actualHours/plannedHours*100)
			#If the value exceeds 100% it means that the operation should have already ended ...
			if expectedProgress>100:
				expectedProgress=100
			if actualProgress > expectedProgress*1.05:
				self.setAttr(name="progressDelay",value="ADVANCED",type="Text")
			else:
				if actualProgress < expectedProgress*0.95:
					self.setAttr(name="progressDelay",value="DELAYED",type="Text")
				else:
					self.setAttr(name="progressDelay",value="NORMAL",type="Text")
		else:
			expectedProgress = 0
			self.setAttr(name="progressDelay",value="Indeterminate",type="Text")

	def compareTimeStams(self, other):
		if self.getTimestamp() > other.getTimestamp():
			return True
		else:
			return False

	def processDelay(self, actualProgress, eventTS):
		
		self.setAttr(name="actualProgress",value=int(actualProgress),type="Number")

		actualHours = float(self.getAttrValue("actualHours"))
		plannedHours = float(self.getAttrValue("plannedHours"))

		if plannedHours > 0:
			expectedProgress = int(actualHours/plannedHours*100)
			#If the value exceeds 100% it means that the operation should have already ended ...
			if expectedProgress>100:
				expectedProgress=100
			if actualProgress > expectedProgress*1.05:
				self.setAttr(name="progressDelay",value="ADVANCED",type="Text")
			else:
				if actualProgress < expectedProgress*0.95:
					self.setAttr(name="progressDelay",value="DELAYED",type="Text")
				else:
					self.setAttr(name="progressDelay",value="NORMAL",type="Text")
		else:
			expectedProgress = 0
			self.setAttr(name="progressDelay",value="Indeterminate",type="Text")

		self.setAttr(name="expectedProgress",value=int(expectedProgress),type="Number")
		self.setAttr(name="statusChangeTS",value=float(eventTS),type="Number")

		attrList = ["actualProgress","expectedProgress","progressDelay","statusChangeTS"]
		self.updateAttrList(attrList)

class Part(Entity):
	def __init__(self,row):
		super().__init__(type="Part",id=int(row["id"]),name="Part",description=row["description"])
		self.part_id = row["id"]
		self.addAttr("partNumber","Text",row["partnumber"])
		self.addAttr("serialNumber","Text",row["serialnumber"])
		self.addAttr("partRev","Text",row["partrev"])
		self.addAttr("cemb","Text",row["cemb"])

	def getID(self):
		return self.part_id

	def getByOperation(self, refOperation):
		return False

	def __eq__(self, other): 
		if not isinstance(other, Part):
			return NotImplemented

		return self.json_entity == other.json_entity

class WorkCenter(Entity):
	def __init__(self,row):
		super().__init__(type="WorkCenter",id=int(row["id"]),name="WorkCenter",description=row["denomination"])
		self.part_id = row["id"]
		self.payload = row

	def __eq__(self, other): 
		if not isinstance(other, WorkCenter):
			return NotImplemented

		return self.payload == other.payload


## Additional debug/verification classes/methods
class TestInfo(Entity):
	def __init__(self,row):
		super().__init__(type="TestInfo",id=1,name="TestInfo",description="Information about the simulation")
		actualStart = datetime.strptime(row["actualstart"], '%Y-%m-%d %H:%M:%S%z')
		self.addAttr("actualStart","Number",actualStart.timestamp())
		actualEnd = datetime.strptime(row["actualend"], '%Y-%m-%d %H:%M:%S%z')
		self.addAttr("actualEnd","Number",actualEnd.timestamp())
		virtualStart = datetime.strptime(row["virtualstart"], '%Y-%m-%d %H:%M:%S%z')
		self.addAttr("virtualStart","Number",virtualStart.timestamp())
		virtualEnd = datetime.strptime(row["virtualend"], '%Y-%m-%d %H:%M:%S%z')
		self.addAttr("virtualEnd","Number",virtualEnd.timestamp())
		self.addAttr("numberOfOrders","Number",row["numberoforders"])
		self.addAttr("numberOfOperations","Number",row["numberofoperations"])
		self.addAttr("operationtotalHours","Number",row["operationstotalhours"])
		self.addAttr("numberOfEvents","Number",row["numberofevents"])
