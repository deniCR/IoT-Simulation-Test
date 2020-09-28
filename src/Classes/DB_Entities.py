import csv
import psycopg2
from datetime import datetime 
import simplejson as json
from psycopg2.extras import RealDictCursor
import os
from termcolor import colored


from . import Entities
from . import Devices

conn = psycopg2.connect("dbname=" + os.environ['DB_NAME'] + " user=" + os.environ['DB_USER'] + " password=" + os.environ['DB_PASSWORD'] + " host=" + os.environ['DB_IP_ADDRESS'] + " port=" + os.environ['DB_PORT_ADDRESS'])

# Read all events from the order and operation files
def readCSV(order_csv_file,operation_csv_file):
	eventDict = {}

	with open(order_csv_file, mode='r') as csv_file:
		order_dict = csv.DictReader(csv_file)
		for row in order_dict:
			ts = (datetime.strptime(row["STATUS_CHANGE_TS"], '%Y/%m/%d %H:%M:%S')).timestamp()
			eventDict.update({ts: Order(row)})

	opEventList={}
	opTotalHours = {}

	with open(operation_csv_file, mode='r') as csv_file:
		operation_dict = csv.DictReader(csv_file)
		for row in operation_dict:
			ts = (datetime.strptime(row["STATUS_CHANGE_TS"], '%Y/%m/%d %H:%M:%S')).timestamp()
			op = Operation(row)
			eventDict.update({ts: op})

			orderNumber = row["ORDER_ID"]
			operationNumber = row["OPER_ID"]

			if not(orderNumber in opEventList):
				opEventList.update({orderNumber: {}})
				opTotalHours.update({orderNumber: {}})

			if not(operationNumber in opEventList[orderNumber]):
				opEventList[orderNumber].update({operationNumber: {}})
				opTotalHours[orderNumber].update({operationNumber: 0})

			opEventList[orderNumber][operationNumber].update({ts: op})

		sensorEvents = {}

		#Set actual totalHours per operation
		for orderN in opEventList:
			for operationN in opEventList[orderN]:
				totalHours = 0.0
				runStart = None
				runEnd = None
				prevEventTS = None

				opEventList[orderN][operationN] = dict(sorted(opEventList[orderN][operationN].items(), key=lambda item: item[0]))

				for ts,opEvent in opEventList[orderN][operationN].items():
					if opEvent.getNewStatus() == "RUN":
						runStart = ts
					if opEvent.getOldStatus() == "RUN":
						runEnd = ts
						if runStart!=None:
							diff = runEnd - runStart
							totalHours += float(diff/3600)
							opEvent.setActualHours(totalHours)
							opTotalHours[orderN][operationN]=totalHours
						else:
							runEnd = None
					prevEventTS = ts

		#Create Sensor events
		for orderN in opEventList:
			for operationN in opEventList[orderN]:
				totalHours = opTotalHours[orderN][operationN]
				runStart = None
				runEnd = None
				prevEventTS = None

				for ts,opEvent in opEventList[orderN][operationN].items():
					if opEvent.getNewStatus() == "RUN":
						runStart = ts
					if opEvent.getOldStatus() == "RUN":
						runEnd = ts
						if runStart!=None:
							eventTS = (prevEventTS + (ts - prevEventTS)/3)
							hoursBefEvent = float(((ts-prevEventTS)/3)/3600)
							newSensorEvent = SensorEvent(opEvent,eventTS,(-hoursBefEvent),totalHours)
							sensorEvents.update({eventTS: newSensorEvent})
						else:
							runEnd = None
					prevEventTS = ts

	sensorEvents = dict(sorted(sensorEvents.items(), key=lambda item: item[0]))

	print(sensorEvents.keys())

	print("\n\n\n\n\n\n\n\n\n\n")

	print(eventDict.keys())

	eventDict = {**sensorEvents,**eventDict}

	eventDict = dict(sorted(eventDict.items(), key=lambda item: item[0]))

	return eventDict,opEventList

# Insert WC, Parts - from csv files
def setStaticEntities(workcenter_file,part_file):
	#Delete/Drop existing tables 
	with conn.cursor() as cur:
		dropTable(cur,'workcenter')
		dropTable(cur,'part')
		dropTable(cur,'order_status_changes')
		dropTable(cur,'operation_status_changes')
		dropTable(cur,'sensor_events')

		print("Drop tables ...")

		cur.execute(workcenter_table)
		print("Create WC table ...")

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

		cur.execute(sensor_event_table)
		print("Create sensor_events table ...")

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
										planedHours DECIMAL,
										scheduledStart TIMESTAMPTZ,
										scheduledEnd TIMESTAMPTZ,
										actualStart VARCHAR(20),
										actualEnd TIMESTAMPTZ,
										site VARCHAR(75),
										totalPlanedHours DECIMAL NOT NULL,
										totalNumberOfOperations DECIMAL NOT NULL,
										statusChangeTS TIMESTAMPTZ NOT NULL,
										id INT GENERATED ALWAYS AS IDENTITY,
										PRIMARY KEY (id),
										CONSTRAINT fk_part FOREIGN KEY (part_id) REFERENCES part(id)
									);
		"""

operation_status_changes_table = 	"""	CREATE TABLE operation_status_changes
										(
											operationNumber VARCHAR(45) NOT NULL,
											workcenter VARCHAR(45) NOT NULL,
											workcenter_id INT NOT NULL,
											orderNumber VARCHAR(45) NOT NULL,
											order_id INT NOT NULL,
											description VARCHAR(175) NOT NULL,
											operationNewStatus VARCHAR(20) NOT NULL,
											operationOldStatus VARCHAR(20) NOT NULL,
											planedHours DECIMAL,
											actualHours DECIMAL,
											statusChangeTS TIMESTAMPTZ NOT NULL,
											id INT GENERATED ALWAYS AS IDENTITY,
											PRIMARY KEY (id),
											CONSTRAINT fk_order FOREIGN KEY (order_id) REFERENCES order_status_changes(id),
											CONSTRAINT fk_workcenter FOREIGN KEY (workcenter_id) REFERENCES workcenter(id)
										);
		"""

sensor_event_table = 	"""	CREATE TABLE sensor_events
							(
								workcenter_id INT NOT NULL,
								operationNumber VARCHAR(75) NOT NULL,
								progress DECIMAL NOT NULL,
								timeStamp TIMESTAMPTZ NOT NULL,
								id INT GENERATED ALWAYS AS IDENTITY,
								PRIMARY KEY (id)
							);
				"""

def dropTable(cur,table):
	cur.execute("select exists(select * from information_schema.tables where table_name=%s)", (table,))
	if(cur.fetchone()[0]):
		cur.execute("DROP TABLE %s CASCADE;" % (table,))

class Order():
	def __init__(self,row):
		self.orderNumber = row["ORDER_ID"]
		self.orderNewStatus = row["NEW_STATUS"]
		self.orderOldStatus = row["OLD_STATUS"]
		self.partNumber = row["PN"]
		if row["SCHEDULE_START_DATE"][0] != ' ':
			self.scheduledStartDate = row["SCHEDULE_START_DATE"]
			#self.scheduledStartDate = datetime.strptime(row["SCHEDULE_START_DATE"], '%Y/%m/%d %H:%M:%S')
		else:
			self.scheduledStartDate = None
		self.scheduledEndDate = None
		
		if row["ACTUAL_START_DATE"][0] != ' ':
			self.actualStart = row["ACTUAL_START_DATE"]
			#self.actualStart = datetime.strptime(row["ACTUAL_START_DATE"], '%Y/%m/%d %H:%M:%S')
		else:
			self.actualStart = None

		self.actualEnd = None
		self.part_id = self.getPartID()
		self.currentOperation = None
		self.planedHours = row["PLANNED_DURATION"]
		self.totalPlanedHours = row["TOTAL_HOURS"]
		self.totalNumberOfOperations = row["TOTAL_OPS"]
		self.site = row["SITE"]
		self.statusChangeTS = datetime.strptime(row["STATUS_CHANGE_TS"], '%Y/%m/%d %H:%M:%S').timestamp()

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

	def complete(self):
		return self.orderNewStatus == "COMPLETE"

	def getOrderNumber(self):
		return self.orderNumber

	def getTimestamp(self):
		return self.statusChangeTS

	def updateDates(self,first_event,start_day,scale):
		if self.scheduledStartDate!=None:
			scheduledStartDate = datetime.strptime(self.scheduledStartDate, '%Y/%m/%d %H:%M:%S')
			diff = scheduledStartDate - first_event
			sum = start_day+diff/scale
			self.scheduledStartDate = sum.strftime('%Y/%m/%d %H:%M:%S')

		if self.actualStart != None:
			actualStart = datetime.strptime(self.actualStart, '%Y/%m/%d %H:%M:%S')
			diff = actualStart - first_event
			sum = start_day+diff/scale
			self.actualStart = sum.strftime('%Y/%m/%d %H:%M:%S')

		if self.totalPlanedHours!=None:
			self.totalPlanedHours = float(self.totalPlanedHours)/scale

		if self.planedHours!=None:
			self.planedHours = float(self.planedHours)/scale

		if self.statusChangeTS != None:
			statusChangeTS = self.statusChangeTS
			diff = statusChangeTS - first_event.timestamp()
			self.statusChangeTS = int(start_day.timestamp()+diff/scale)

	def update(self,attr,value):
		with conn.cursor() as cur:
			cur.execute("""UPDATE order_status_changes SET %s = %s WHERE order_id = %s;""",(attr,value,self.order_id))

	def setTimestamps(self, newTime):
		self.statusChangeTS = newTime

		if self.orderNewStatus == "COMPLETE" or self.orderNewStatus == "CANCELLED":
			self.actualEnd = newTime

	def insert(self):
		if(self.orderNumber.isdigit()):
			print(colored("INSERT ORDER: ","green") + self.orderNumber)
			with conn.cursor() as cur:
				cur.execute("""INSERT INTO order_status_changes VALUES 
					(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
					""",(self.orderNumber,self.currentOperation,self.partNumber,self.part_id,
						self.orderNewStatus,self.orderOldStatus,self.planedHours,self.scheduledStartDate,
						self.scheduledEndDate,self.actualStart,self.actualEnd,self.site,self.totalPlanedHours,
						self.totalNumberOfOperations,datetime.fromtimestamp(self.statusChangeTS)))

			conn.commit()
			return True
		else:
			return False

class SensorEvent():
	def __init__(self,opEvent,timestamp,hoursAftEvent,totalHours):
		self.workcenter=opEvent.getWorkCenterID()
		self.operationNumber=opEvent.getOperationNumber()
		self.timestamp = timestamp

		opActualHours=opEvent.getActualHours()+hoursAftEvent
		opTotalHours=totalHours
		self.percentage = (opActualHours/opTotalHours)*100

	def updateDates(self,first_event,start_day,scale):

		if self.timestamp != None:
			timestamp = self.timestamp
			diff = timestamp - first_event.timestamp()
			sum_time = start_day.timestamp()+diff/scale
			self.timestamp = sum_time

	def getTimestamp(self):
		return self.timestamp

	def insert(self):
		with conn.cursor() as cur:
			cur.execute("""INSERT INTO sensor_events VALUES (%s, %s, %s, %s)""",(self.workcenter,self.operationNumber,self.percentage,datetime.fromtimestamp(self.timestamp,)))
		conn.commit()
		return True

class Operation():
	def __init__(self,row):
		self.operation_id = row["OPER_ID"]
		self.operationNumber = row["OPER_ID"]
		self.description = row["OPER_DESC"]
		self.partNumber = row["PN"]
		self.operationNewStatus = row["NEW_STATUS"]
		self.operationOldStatus = row["OLD_STATUS"]
		self.site = row["SITE"]
		self.actualHours = 0

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
				#self.order_id = None
				#create new order with order_id == self.order ...
				data = {}
				data.update({"ORDER_ID": self.order})
				data.update({"NEW_STATUS": "-"})
				data.update({"OLD_STATUS": "-"})
				data.update({"SCHEDULE_START_DATE": " "})
				data.update({"PN": "-"})
				data.update({"ACTUAL_START_DATE": " "})
				data.update({"PLANNED_DURATION": 0})
				data.update({"TOTAL_HOURS": 0})
				data.update({"TOTAL_OPS": 1})
				data.update({"SITE": "-"})
				order_ts = datetime.now()
				data.update({"STATUS_CHANGE_TS": datetime.strftime(order_ts, '%Y/%m/%d %H:%M:%S')})

				newOrder = Order(data)
				newOrder.insert()

		opHours = row["PLANNED_DURATION"]
		if not(opHours.isdigit()):
			hours = opHours.split('-')
			size = len(hours)
			average = 0
			for h in hours:
				average = average + float(h)
			average = average/size
			opHours = average
		
		self.planedHours = float(opHours)
		#self.statusChangeTS = row ["STATUS_CHANGE_TS"]
		self.statusChangeTS = datetime.strptime(row["STATUS_CHANGE_TS"], '%Y/%m/%d %H:%M:%S').timestamp()

	def updateDates(self,first_event,start_day,scale):

		if self.actualHours!=None:
			self.actualHours = float(self.actualHours)/scale

		if self.planedHours!=None:
			self.planedHours = float(self.planedHours)/scale

		if self.statusChangeTS != None:
			statusChangeTS = self.statusChangeTS
			diff = statusChangeTS - first_event.timestamp()
			self.statusChangeTS = start_day.timestamp()+diff/scale

	def getOrderID(self):
		return self.id[:18]

	def getOrderNumber(self):
		return self.order

	def getOperationID(self):
		return self.id[:22]

	def getWorkCenterID(self):
		return self.workcenter_id

	def getWorkCenter(self):
		return self.workcenter

	def getOperationNumber(self):
		return self.operationNumber

	def getOperationDescription(self):
		return self.description

	def getPlanedHours(self):
		return self.planedDuration

	def getActualHours(self):
		return self.actualHours

	def getTimestamp(self):
		return self.statusChangeTS

	def setTimestamps(self, newTime):
		self.statusChangeTS = newTime

	def setStatus(self, newStatus):
		self.operationNewStatus = newStatus

	def setActualHours(self, hours):
		self.actualHours = hours

	def getOldStatus(self):
		return self.operationOldStatus

	def getNewStatus(self):
		return self.operationNewStatus

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

		if(self.order_id != None and self.operation_id.isdigit()):

			print(colored("INSERT OPERATION: ","green") + self.operation_id)

			with conn.cursor() as cur:
				cur.execute("""INSERT INTO operation_status_changes VALUES 
						(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
						""",(self.operation_id,self.workcenter,self.workcenter_id,self.order,self.order_id,self.description,
							self.operationNewStatus,self.operationOldStatus,"{:.4f}".format(self.planedHours),"{:.4f}".format(self.actualHours),datetime.fromtimestamp(self.statusChangeTS)))
			conn.commit()
			return True
		else:
			print(colored("Failde to insert Operations: ","red") + self.operation_id)

		return False

def readWorkCenter(known_WorkCenters):
	WorkCenterList = {}
	with conn.cursor(cursor_factory=RealDictCursor) as cur:
		if known_WorkCenters != None:
			cur.execute("SELECT * FROM workcenter WHERE id NOT IN " + known_WorkCenters + ";")
		else:
			cur.execute("SELECT * FROM workcenter;")
		data = cur.fetchall()

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

def readNewOrders(knownOrders, time):
	OrderList = {}
	with conn.cursor(cursor_factory=RealDictCursor) as cur:
		if knownOrders != None:
			cur.execute("SELECT * FROM order_status_changes WHERE statuschangets >= (NOW() - interval '" + str(time) + " seconds') AND ordernumber NOT IN " + knownOrders + " AND orderNumber NOT IN (SELECT orders_ended()) ORDER BY statuschangets desc;")
		else:
			cur.execute("SELECT * FROM order_status_changes WHERE statuschangets >= (NOW() - interval '" + str(time) + " seconds') AND orderNumber NOT IN (SELECT orders_ended()) ORDER BY statuschangets desc;")
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

def collectKnownOrders(knownOrders, time):
	OrderList = {}
	with conn.cursor(cursor_factory=RealDictCursor) as cur:

		if knownOrders != None:

			cur.execute("SELECT * FROM order_status_changes WHERE statuschangets >= (NOW() - interval '" + str(time) + " seconds') AND ordernumber in " + knownOrders + " ORDER BY statuschangets desc;")
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

# Completed or canceled operations are ignored
def readNewOperation(orderNumber, known_Operations, time):
	OperationList = {}
	with conn.cursor(cursor_factory=RealDictCursor) as cur:

		known_Ops = None
		if(orderNumber in known_Operations):
			known_Ops = known_Operations[orderNumber]

		if known_Ops != None:
			cur.execute("SELECT * FROM operation_status_changes WHERE statuschangets >= (NOW() - interval '" + str(time) + " seconds') AND operationnumber NOT IN " + known_Ops + " AND (operationnumber NOT IN (SELECT operations_ended('" + str(orderNumber) + "'))) AND ordernumber = '" + str(orderNumber) + "' ORDER BY statuschangets desc;")
		else:
			cur.execute("SELECT * FROM operation_status_changes WHERE statuschangets >= (NOW() - interval '" + str(time) + " seconds') AND ordernumber = '" + str(orderNumber) + "' AND (operationnumber NOT IN (SELECT operations_ended('" + str(orderNumber) + "'))) ORDER BY statuschangets desc;")
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

def collectKnownOperations(orderNumber, known_Operations, time):
	OperationList = {}
	with conn.cursor(cursor_factory=RealDictCursor) as cur:

		known_Ops = None
		if(orderNumber in known_Operations):
			known_Ops = known_Operations[orderNumber]

		if known_Ops != None:
			cur.execute("SELECT * FROM operation_status_changes WHERE statuschangets >= (NOW() - interval '" + str(time) + " seconds') AND operationnumber IN " + known_Ops + " AND ordernumber = '" + str(orderNumber) + "' ORDER BY statuschangets desc;")
		else:
			cur.execute("SELECT * FROM operation_status_changes WHERE statuschangets >= (NOW() - interval '" + str(time) + " seconds') AND ordernumber = '" + str(orderNumber) + "' ORDER BY statuschangets desc;")
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

def readNumberOfEndedOperations(orderNumber):
	data = None
	with conn.cursor(cursor_factory=RealDictCursor) as cur:
		cur.execute("SELECT numberofoperationsended(%s);",(str(orderNumber),))
		data = cur.fetchone()["numberofoperationsended"]

	return data

def readTotalActualHours(orderNumber):
	data = None
	with conn.cursor(cursor_factory=RealDictCursor) as cur:
		cur.execute("SELECT total_actual_hours(%s);",(str(orderNumber),))
		data = cur.fetchone()["total_actual_hours"]

	return data

def readNewSensorEvents(lastID):

	protocol = "PDI-IoTA-UltraLight"
	apikey = "hfe9iuh83qw9hr8ew9her9"
	ref = "/iot/d"

	SensorEvList = {}
	with conn.cursor(cursor_factory=RealDictCursor) as cur:
		cur.execute("SELECT * FROM sensor_events WHERE id > " + str(lastID) + " LIMIT 30;")
		data = cur.fetchall()

		for sensor_ev in data:
			decode = json.dumps(sensor_ev, indent=2, default=str)
			encode = json.loads(decode)
			ev = None
			ev = Devices.ProgressSensor(0)
			
			if ev.loadDBEntry(protocol,apikey,ref,encode):
				id = encode["id"]
				SensorEvList.update({id: ev})

	return SensorEvList
