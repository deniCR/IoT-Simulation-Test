import csv
import postgresql
import psycopg2
import datetime
from time import sleep
from datetime import date
import simplejson as json
from psycopg2.extras import RealDictCursor
import os

import Classes.Entities as Entities

conn = psycopg2.connect("dbname=MES-DB user=postgres host=" + os.environ['DB_IP_ADDRESS'] + " port=" + os.environ['DB_PORT_ADDRESS'])

# Read csv files
def readCSV(order,operation):
	eventDict = {}
	#operation_count = 0
	#order_count = 0
	#orderDict = {}
	#operationDict = {}

	with open(order, mode='r') as csv_file:
		order_dict = csv.DictReader(csv_file)
		for row in order_dict:
			ts = datetime.datetime.strptime(row["STATUS_CHANGE_TS"], '%Y/%m/%d %H:%M:%S')
			eventDict.update({ts: Order(row)})

	with open(operation, mode='r') as csv_file:
		operation_dict = csv.DictReader(csv_file)
		for row in operation_dict:
			ts = datetime.datetime.strptime(row["STATUS_CHANGE_TS"], '%Y/%m/%d %H:%M:%S')
			eventDict.update({ts: Operation(row)})

	eventDict = dict(sorted(eventDict.items(), key=lambda item: item[0]))

#	with open(operation, mode='r') as csv_file:
#		operation_dict = csv.DictReader(csv_file)
#		for row in operation_dict:
#			if not row["ORDER_ID"] in operationDict:
#				operationDict.update({row["ORDER_ID"]: {}})
#			if not row["OPER_ID"] in operationDict[row["ORDER_ID"]]:
#				operationDict[row["ORDER_ID"]].update({row["OPER_ID"]: {}})
#			operationDict[row["ORDER_ID"]][row["OPER_ID"]].update({row["STATUS_CHANGE_TS"]: Operation(row)})
#			operation_count += operation_count + 1
#
#		with open(order, mode='r') as csv_file:
#			order_dict = csv.DictReader(csv_file)
#			for row in order_dict:
#				#List of operations associated with this order
#				operation_list = []
#
#				if row["ORDER_ID"] in operationDict: # ??? Podem existir orders sem operações no dataset ....
#					for op in operationDict[row["ORDER_ID"]].values():
#						operation_list.append(op)
#
#				if not row["ORDER_ID"] in orderDict:
#					orderDict.update({row["ORDER_ID"]: {}})
#				orderDict[row["ORDER_ID"]].update({order_count: Order(row,operation_list)})
#				order_count += order_count + 1

	#return orderDict,operationDict
	return eventDict

# Insert WC, Operation, Parts
# ??? - remove the use of conn and cur ...
def setStaticEntities(workcenter_file,part_file):
	#Delete/Drop existing tables 
	with conn.cursor() as cur:
		dropTable(cur,'workcenter')
		dropTable(cur,'part')
		dropTable(cur,'order_status_changes')
		dropTable(cur,'operation_status_changes')

		print("Drop tables ...")

		cur.execute(workcenter_table)
		print("Create WC table ...")

		#with open(workcenter_file, 'r') as f:
		#	reader = csv.reader(f)
		#	next(reader) # Skip the header row.
		#	for row in reader:
		#		cur.execute(
		#		"INSERT INTO workcenter VALUES (%s)",
		#		row[1]
		#	)
		#	f.close()

		cur.execute(part_table)
		print("Create Part table ...")

		with open(part_file, 'r') as f:
			reader = csv.reader(f)
			next(reader) # Skip the header row.
			for row in reader:
				cur.execute(
				"INSERT INTO part VALUES (%s, %s, %s, %s, %s)",
				row
			)
			f.close()

		cur.execute(order_status_changes_table)
		print("Create Order table ...")

		cur.execute(operation_status_changes_table)
		print("Create Operation table ...")

	conn.commit()

workcenter_table = """	CREATE TABLE workcenter
					(
						denomination VARCHAR(75) NOT NULL,
						id INT GENERATED ALWAYS AS IDENTITY,
						PRIMARY KEY (id)
					);
					"""

part_table = 	"""	CREATE TABLE part
					(
						partNumber VARCHAR(75) NOT NULL,
						serialNumber VARCHAR(75) NOT NULL,
						description VARCHAR(75) NOT NULL,
						partRev VARCHAR(75) NOT NULL,
						cemb VARCHAR(75) NOT NULL,
						planedHours DECIMAL,
						id INT GENERATED ALWAYS AS IDENTITY,
						PRIMARY KEY (id)
					);
				"""

order_status_changes_table = 	"""	CREATE TABLE order_status_changes
			(
				orderNumber VARCHAR(45) NOT NULL,
				currentOperation INT,
				partNumber VARCHAR(45),
				part_id INT,
				orderNewStatus VARCHAR(20) NOT NULL,
				orderOldStatus VARCHAR(20) NOT NULL,
				planedHours DECIMAL NOT NULL,
				scheduledStart TIMESTAMP,
				scheduledEnd TIMESTAMP,
				actualStart VARCHAR(20),
				actualEnd VARCHAR(20),
				site VARCHAR(75),
				statusChangeTS TIMESTAMP,
				id INT GENERATED ALWAYS AS IDENTITY,
				PRIMARY KEY (id),
				CONSTRAINT fk_part FOREIGN KEY (part_id) REFERENCES part(id)
			);
		"""

operation_status_changes_table = 	"""	CREATE TABLE operation_status_changes
			(
				operationNumber VARCHAR(45),
				workcenter VARCHAR(45),
				workcenter_id INT,
				orderNumber VARCHAR(45),
				order_id INT,
				description VARCHAR(175),
				operationNewStatus VARCHAR(20) NOT NULL,
				operationOldStatus VARCHAR(20) NOT NULL,
				planedHours DECIMAL NOT NULL,
				statusChangeTS TIMESTAMP,
				id INT GENERATED ALWAYS AS IDENTITY,
				PRIMARY KEY (id),
				CONSTRAINT fk_order FOREIGN KEY (order_id) REFERENCES order_status_changes(id),
				CONSTRAINT fk_workcenter FOREIGN KEY (workcenter_id) REFERENCES workcenter(id)
			);
		"""

def dropTable(cur,table):
	cur.execute("select exists(select * from information_schema.tables where table_name=%s)", (table,))
	if(cur.fetchone()[0]):
		cur.execute("DROP TABLE %s CASCADE;" % (table,))

#Deprecated ...
#def importDataCSV(cur, table, file):
#	with open(file, 'r') as f:
#		reader = csv.reader(f)
#		next(reader) # Skip the header
#		for row in reader:
#			cur.execute("INSERT INTO %s VALUES (%s, %s)",(table,row[0],row[1]))

#class wc ...
#class part ...

class Order():
	def __init__(self,row):
		self.orderNumber = row["ORDER_ID"]
		#self.orderDescription = row["OPER_DESC"]
		#self.description = row["DESCRIPTION"]
		#self.shopOrder = row["SHOP_ORDER_#"]
		#self.category = row["CATEGORY"]
		self.orderNewStatus = row["NEW_STATUS"]
		self.orderOldStatus = row["OLD_STATUS"]
		#self.cemb = row["CEMB"]
		self.partNumber = row["PN"]
		#self.serialNumber = row["SO_SERIAL_NUMBER"]
		if row["SCHEDULE_START_DATE"][0] != ' ':
			self.scheduledStartDate = row["SCHEDULE_START_DATE"]
		else:
			self.scheduledStartDate = None
		self.scheduledEndDate = None
		#self.scheduledStart = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		#self.scheduledEnd = (datetime.datetime.now() + datetime.timedelta(0, 60)).strftime('%Y-%m-%d %H:%M:%S')
		if row["ACTUAL_START_DATE"][0] != ' ':
			self.actualStart = row["ACTUAL_START_DATE"]
		else:
			self.actualStart = None

		self.actualEnd = None

		#print("Self part Number: " + self.partNumber)

		self.part_id = self.getPartID()

#		self.operation_list = operations

		self.currentOperation = None #CHANGE TO NULL value ...

		self.planedHours = row["PLANNED_DURATION"]

#		self.numberOfOperations = len(operations)

		self.site = row["SITE"]
		self.statusChangeTS = row ["STATUS_CHANGE_TS"]

	def getPartID(self):
		with conn.cursor() as cur:
			if self.partNumber!= None:
				cur.execute("""SELECT id
							FROM part
							WHERE partnumber = %s; 
						""",(self.partNumber,))

			part_id = cur.fetchone()

			if part_id != None:
				self.part_id = part_id[0]
			else:
				self.part_id = 0 # NULL 

	def completed(self):
		return self.orderNewStatus == "COMPLETED"

	def getOrderNumber(self):
		return self.orderNumber

	def getTimestamp(self):
		return self.statusChangeTS

	def setTimestamp(self, newTime):
		self.statusChangeTS = newTime

	def updateDates(self,start_day,scale):
		if self.scheduledStartDate!=None:
			scheduledStartDate = datetime.datetime.strptime(self.scheduledStartDate, '%Y/%m/%d %H:%M:%S')
			diff = scheduledStartDate - start_day
			self.scheduledStartDate = (start_day+diff/scale).strftime('%Y/%m/%d %H:%M:%S')

		if self.actualStart != None:
			actualStart = datetime.datetime.strptime(self.actualStart, '%Y/%m/%d %H:%M:%S')
			diff = actualStart - start_day
			self.actualStart = (start_day+diff/scale).strftime('%Y/%m/%d %H:%M:%S')


#	def nextOperation(self):
#		end = 1
#
#		#Start Order
#		if self.orderNewStatus == "SCHEDULED":
#			self.orderNewStatus = "RUN"
#			self.actualStart = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#			with conn.cursor() as cur:
#				cur.execute("""UPDATE order_status_changes SET orderNewStatus = 'RUN' WHERE order_id = %s;""",(self.order_id,))
#				cur.execute("""UPDATE order_status_changes SET actualStart = %s WHERE order_id = %s;""",(self.actualStart,self.order_id,))
#
#			#Start the first operation
#			self.currentOperation = self.operation_list[0]
#			self.currentOperation.setStatus("RUN")
#			self.currentOperation.update("operationNewStatus","RUN")
#			self.operation_list.remove(self.currentOperation)
#		#Order already in execution
#		else:
#			if self.orderNewStatus == "RUN":
#
#				#Complete the currentOperation
#				self.currentOperation.setStatus("COMPLETED")
#				self.currentOperation.update("operationNewStatus","COMPLETED")
#
#				#There are more operations to be executed
#				if len(self.operation_list) > 0:
#					#Change the current operation(COMPLETED) for the next operation of the order
#					self.currentOperation = self.operation_list[0]
#					self.currentOperation.setStatus("RUN")
#					self.currentOperation.update("operationNewStatus","RUN")
#					self.operation_list.remove(self.currentOperation)
#
#					#Update the current operation (to the new current operation)
#					with conn.cursor() as cur:
#						cur.execute("""UPDATE order_status_changes SET currentOperation = %s WHERE order_id = %s;
#								""" % (self.currentOperation.getOperationID(),self.order_id,))
#				#All the operations are completed
#				else:
#					self.actualEnd = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#					with conn.cursor() as cur:
#						cur.execute("""UPDATE order_status_changes SET orderNewStatus = 'COMPLETED' WHERE order_id = %s;""",(self.order_id,))
#						cur.execute("""UPDATE order_status_changes SET actualEnd = %s WHERE order_id = %s;""",(self.actualEnd,self.order_id,))
#					end = 0
#
#		conn.commit()
#		return end

	def update(attr,value):
		with conn.cursor() as cur:
			cur.execute("""UPDATE order_status_changes SET %s = %s WHERE order_id = %s;""",(attr,value,self.order_id))

	def insert(self):
		with conn.cursor() as cur:
			cur.execute("""INSERT INTO order_status_changes VALUES 
				(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
				""",(self.orderNumber,self.currentOperation,self.partNumber,self.part_id,
					self.orderNewStatus,self.orderOldStatus,self.planedHours,self.scheduledStartDate,
					self.scheduledEndDate,self.actualStart,self.actualEnd,self.site,self.statusChangeTS))

		conn.commit()
		return True


class Operation():
	def __init__(self,row):
		self.operation_id = row["OPER_ID"]
		self.operationNumber = row["OPER_ID"] # ??? - GET THE NEW ID
#		self.workcenter_id = row["WC"]
		self.description = row["OPER_DESC"]
		self.partNumber = row["PN"]
#		self.operationStatus = row["OPERATION_STATUS"]
		self.operationNewStatus = row["NEW_STATUS"]
		self.operationOldStatus = row["OLD_STATUS"]
		#if row["FIRST_RUN_DATE"] != '':
		#	self.fristRunDate = row["FIRST_RUN_DATE"]
		#else:
		#	self.fristRunDate = None
		#if row["COMPLETE_DATE"] != '':
		#	self.completeRunDate = row["COMPLETE_DATE"]
		#else:
		#	self.completeRunDate = None
		#self.batch = row["BATCH"]
		#self.quantity = row["Basic_Qty"]
		#self.setupMan = row["Setup_Man"]
		#self.manPowerHours = row["Man_Power_Hours"]
		#self.setupMachine = row["Setup_Machine"]
		#self.machineHours = row["Machine_Hours"]

		self.site = row["SITE"]

		self.workcenter = row["WORKCENTER"]
		workcenter_id = None
		with conn.cursor() as cur:
			cur.execute("""SELECT id
						FROM workcenter
						WHERE denomination = %s; 
					""",(self.workcenter,))
			workcenter_id = cur.fetchone()

		if workcenter_id != None:
			self.workcenter_id = workcenter_id[0]
		else:
			with conn.cursor() as cur:
				cur.execute("""INSERT INTO workcenter
					VALUES (%s)
						""",(self.workcenter,))
				cur.execute("""SELECT id
							FROM workcenter
							WHERE denomination = %s; 
						""",(self.workcenter,))
				workcenter_id = cur.fetchone()
			self.workcenter_id = workcenter_id[0]

		self.order = row["ORDER_ID"]
		with conn.cursor() as cur:
			cur.execute("""SELECT id
						FROM order_status_changes
						WHERE ordernumber = %s; 
					""",(self.order,))
			order_id = cur.fetchone()
			if order_id != None:
				self.order_id = order_id[0]
			else:
				self.order_id = None

		#self.planedHours = float(self.setupMan) + float(self.manPowerHours) + float(self.setupMachine) + float(self.machineHours)
		
		self.planedHours = float(str(row["PLANNED_DURATION"]).replace("-","."))

		self.statusChangeTS = row ["STATUS_CHANGE_TS"]

	def getOrderID(self):
		return self.id[:18]

	def getOrderNumber(self):
		return self.order

	def getOperationID(self):
		return self.id[:22]

	def getOperationNumber(self):
		return self.operationNumber

	def getOperationDescription(self):
		return self.description

	def getOperationID(self):
		return self.operation_id

	def getPlanedHours(self):
		return self.planedDuration

	def getTimestamp(self):
		return self.statusChangeTS

	def setTimestamp(self, newTime):
		self.statusChangeTS = newTime

	def setStatus(self, newStatus):
		self.operationNewStatus = newStatus

	def update(self,attr,value):
		with conn.cursor() as cur:
			cur.execute("UPDATE operation_status_changes SET " + attr +  """= %s WHERE operation_id = %s;""",(value,self.operation_id,))
		conn.commit()

	def insert(self):

		with conn.cursor() as cur:
			cur.execute("""SELECT id
						FROM order_status_changes
						WHERE ordernumber = %s; 
					""",(self.order,))
			order_id = cur.fetchone()
			if order_id != None:
				self.order_id = order_id[0]
			else:
				self.order_id = None

		if(self.order_id != None):

			with conn.cursor() as cur:
				cur.execute("""INSERT INTO operation_status_changes VALUES 
						(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
						""",(self.operation_id,self.workcenter,self.workcenter_id,self.order,self.order_id,self.description,
							self.operationNewStatus,self.operationOldStatus,"{:.2f}".format(5,self.planedHours),self.statusChangeTS))
			conn.commit()
			return True

		return False

operation_status_changes_table = 	"""	CREATE TABLE operation_status_changes
			(
				operationNumber VARCHAR(45),
				workcenter VARCHAR(45),
				workcenter_id INT,
				orderNumber VARCHAR(45),
				order_id INT,
				description VARCHAR(175),
				operationNewStatus VARCHAR(20) NOT NULL,
				operationOldStatus VARCHAR(20) NOT NULL,
				planedHours DECIMAL NOT NULL,
				statusChangeTS TIMESTAMP,
				id INT GENERATED ALWAYS AS IDENTITY,
				PRIMARY KEY (id),
				CONSTRAINT fk_order FOREIGN KEY (order_id) REFERENCES order_status_changes(id),
				CONSTRAINT fk_workcenter FOREIGN KEY (workcenter_id) REFERENCES workcenter(id)
			);
		"""

def readWorkCenter(known_WorkCenters):
	WorkCenterList = {}
	with conn.cursor(cursor_factory=RealDictCursor) as cur:
		if known_WorkCenters != None:
			cur.execute("SELECT * FROM workcenter WHERE id NOT IN " + known_WorkCenters + ";")
		else:
			cur.execute("SELECT * FROM workcenter;")
		data = cur.fetchall()

		orders_payload = json.dumps(data, indent=2, default=str)
		for order in data:
			decode = json.dumps(order, indent=2, default=str)
			encode = json.loads(decode)
			WorkCenterList.update({encode["id"]: Entities.WorkCenter(encode)})

	return WorkCenterList

def readPart(known_Parts):
	PartList = {}
	with conn.cursor(cursor_factory=RealDictCursor) as cur:
		if known_Parts != None:
			cur.execute("SELECT * FROM part WHERE id NOT IN " + known_Parts + ";")
		else:
			cur.execute("SELECT * FROM part;")
		data = cur.fetchall()

		for part in data:
			decode = json.dumps(part, indent=2, default=str)
			encode = json.loads(decode)
			PartList.update({encode["id"]: Entities.Part(encode)})

	return PartList

def readNewOrders(knownOrders):
	OrderList = {}
	with conn.cursor(cursor_factory=RealDictCursor) as cur:
		if knownOrders != None:
			cur.execute("SELECT * FROM order_status_changes WHERE ordernumber NOT IN " + knownOrders + " AND orderNumber NOT IN (SELECT orders_ended()) LIMIT 100;")
		else:
			cur.execute("SELECT * FROM order_status_changes LIMIT 25;")
		data = cur.fetchall()

		for order in data:
			decode = json.dumps(order, indent=2, default=str)
			encode = json.loads(decode)
			ord = None
			ord = Entities.Order()
			ord.loadDBEntry(encode)

			orderNumber = ord.getOrderID()

			#Get only the last update/statusChanges Or get all the updates and insert the updates in order ???
			if orderNumber in OrderList:
				if OrderList[orderNumber].getTimeStamp() < ord.getTimeStamp():
					OrderList[orderNumber]=ord
			else:
				OrderList.update({orderNumber: ord})

	return OrderList

def collectKnownOrders(knownOrders):
	OrderList = {}
	with conn.cursor(cursor_factory=RealDictCursor) as cur:

		if knownOrders != None:

			cur.execute("SELECT * FROM order_status_changes WHERE ordernumber in " + knownOrders + " LIMIT 100;")
			data = cur.fetchall()

			for order in data:
				decode = json.dumps(order, indent=2, default=str)
				encode = json.loads(decode)
				ord = None
				ord = Entities.Order()
				ord.loadDBEntry(encode)

				orderNumber = ord.getOrderID()

				#Get only the last update/statusChanges Or get all the updates and insert the updates in order ???
				if orderNumber in OrderList:
					if OrderList[orderNumber].getTimeStamp() < ord.getTimeStamp():
						OrderList[orderNumber]=ord
				else:
					OrderList.update({orderNumber: ord})

	return OrderList

def readNewOperation(orderNumber, known_Operations):
	OperationList = {}
	with conn.cursor(cursor_factory=RealDictCursor) as cur:

		known_Ops = None
		if(orderNumber in known_Operations):
			known_Ops = known_Operations[orderNumber]

		if known_Ops != None:
			cur.execute("SELECT * FROM operation_status_changes WHERE operationnumber NOT IN " + known_Ops + " AND ordernumber = %s AND operationNumber NOT IN (SELECT operations_ended());",(str(orderNumber),))
		else:
			cur.execute("SELECT * FROM operation_status_changes WHERE ordernumber = %s;",(str(orderNumber),))
		data = cur.fetchall()

		for operation in data:
			decode = json.dumps(operation, indent=2, default=str)
			encode = json.loads(decode)
			op = Entities.Operation()
			op.loadDBEntry(encode)

			operationNumber = op.getOperationID()

			#Get only the last update/statusChanges Or get all the updates and insert the updates in order ???
			if operationNumber in OperationList:
				if OperationList[operationNumber].getTimeStamp() < op.getTimeStamp():
					OperationList[operationNumber] = op
			else:
				OperationList.update({operationNumber: op})

	return OperationList

def collectKnownOperations(orderNumber, known_Operations):
	OperationList = {}
	with conn.cursor(cursor_factory=RealDictCursor) as cur:

		known_Ops = None
		if(orderNumber in known_Operations):
			known_Ops = known_Operations[orderNumber]

		if known_Ops != None:
			cur.execute("SELECT * FROM operation_status_changes WHERE operationnumber IN " + known_Ops + " AND ordernumber = %s;",(str(orderNumber),))
		else:
			cur.execute("SELECT * FROM operation_status_changes WHERE ordernumber = %s;",(str(orderNumber),))
		data = cur.fetchall()

		orders_payload = json.dumps(data, indent=2, default=str)
		for operation in data:
			decode = json.dumps(operation, indent=2, default=str)
			encode = json.loads(decode)
			op = Entities.Operation()
			op.loadDBEntry(encode)

			operationNumber = op.getOperationID()

			#Get only the last update/statusChanges Or get all the updates and insert the updates in order ???
			if operationNumber in OperationList:
				if OperationList[operationNumber].getTimeStamp() < op.getTimeStamp():
					OperationList[operationNumber] = op
			else:
				OperationList.update({operationNumber: op})

	return OperationList

def readNumberOfTotalOperations(orderNumber):
	data = None
	with conn.cursor(cursor_factory=RealDictCursor) as cur:
		cur.execute("SELECT numberoftotaloperations(%s);",(str(orderNumber),))
		data = cur.fetchone()["numberoftotaloperations"]

	return data

def readNumberOfEndedOperations(orderNumber):
	data = None
	with conn.cursor(cursor_factory=RealDictCursor) as cur:
		cur.execute("SELECT numberofoperationsended(%s);",(str(orderNumber),))
		data = cur.fetchone()["numberofoperationsended"]

	return data