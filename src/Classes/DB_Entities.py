import csv
import psycopg2
from datetime import datetime 
import simplejson as json
from psycopg2.extras import RealDictCursor
import os

from . import Entities
from . import Devices

conn = psycopg2.connect("dbname=" + os.environ['POSTGRES_DB'] + " user=" + os.environ['POSTGRES_USER'] + " password=" + os.environ['POSTGRES_PASSWORD'] + " host=" + os.environ['POSTGRES_IP'] + " port=" + os.environ['POSTGRES_PORT'])

# Read all events from the order and operation files
def readCSV(order_csv_file,operation_csv_file):
	eventDict = {}
	orderDict = {}
	orderList = {}
	orderTotalHours = {}
	orderPlannedHours = {}

	#Open and read from the order_csv_file
	with open(order_csv_file, mode='r') as csv_file:
		aux_dict = csv.DictReader(csv_file)
		aux_count=0
		for row in aux_dict:
			aux_count+=1
			ts = (datetime.strptime(row["STATUS_CHANGE_TS"], '%Y/%m/%d %H:%M:%S')).timestamp()
			order = Order(row)

			while ts in eventDict:
				ts+=0.1
			eventDict.update({ts: order})

			orderNumber = row["ORDER_ID"]

			if not(orderNumber in orderList):
				orderList.update({orderNumber: {}})
				orderTotalHours.update({orderNumber: 0})
				orderPlannedHours.update({orderNumber: 0})

			orderList[orderNumber].update({ts: order})

		print("Number of order event readed: " + str(len(eventDict)) + " vs counter: " + str(aux_count))

	numberOfOperations = 0
	opEventList={}
	opTotalHours = {}
	opRunTimeIntervals= {}

	#Open and read from the operation_csv_file
	with open(operation_csv_file, mode='r') as csv_file:
		aux_dict = csv.DictReader(csv_file)
		for row in aux_dict:
			aux_count+=1
			ts = (datetime.strptime(row["STATUS_CHANGE_TS"], '%Y/%m/%d %H:%M:%S')).timestamp()
			op = Operation(row)

			while ts in eventDict:
				ts+=0.1
			eventDict.update({ts: op})

			orderNumber = row["ORDER_ID"]
			operationNumber = row["OPER_ID"]

			if not(orderNumber in opEventList):
				opEventList.update({orderNumber: {}})
				opTotalHours.update({orderNumber: {}})
				opRunTimeIntervals.update({orderNumber: {}})
			if not(operationNumber in opEventList[orderNumber]):
				opEventList[orderNumber].update({operationNumber: {}})
				opTotalHours[orderNumber].update({operationNumber: 0})
				opRunTimeIntervals[orderNumber].update({operationNumber: 0})
				numberOfOperations+=1
			opEventList[orderNumber][operationNumber].update({ts: op})

			newOrderEv=None
			#Check if there are prior OrderEvents to this operation
			if orderNumber in orderList:
				o_ts,newOrderEv=checkPrevOrderEvents(op,orderList[orderNumber])
			else:
				orderList.update({orderNumber: {}})
				o_ts,newOrderEv=checkPrevOrderEvents(op,None)

			if newOrderEv!=None:
				#Add the newOrderEvent
				while o_ts in eventDict:
					o_ts+=0.1
				eventDict.update({o_ts: newOrderEv})
				orderList[orderNumber].update({o_ts: newOrderEv})
				aux_count+=1

		for orderN in orderList:
			first_event = min(orderList[orderN])
			last_event = max(orderList[orderN])
			interval = last_event-first_event
			real_interval = orderList[orderN][last_event].getTimestamp() - orderList[orderN][first_event].getTimestamp() 
			first_event_status = orderList[orderN][first_event].getNewStatus()
			last_event_status = orderList[orderN][last_event].getNewStatus()
			if (real_interval < 1800 and last_event_status in ("CANCELLED","COMPLETE")) or (first_event in ("CANCELLED","COMPLETE")):
				print("ORDER COMPLETE ..." + str(orderN))
				print(str(real_interval))
				for ts,order in orderList[orderN].items():
					print("\t" + str(ts) + " " + str(order.getNewStatus()))
				print("\n")

		print("Number of orderEvents + opEvents readed: " + str(len(eventDict)) + " vs counter: " + str(aux_count))

		#Set actual totalHours per operation and order
		for orderN in opEventList:

			if not (orderN in orderTotalHours):
				orderTotalHours.update({orderN: 0})
				orderPlannedHours.update({orderN: 0})

			for operationN in opEventList[orderN]:
				totalHours = 0.0
				runTimeIntervals = 0
				runStart = None
				runEnd = None

				opEventList[orderN][operationN] = dict(sorted(opEventList[orderN][operationN].items(), key=lambda item: item[0]))

				for ts,opEvent in opEventList[orderN][operationN].items():
					if opEvent.getNewStatus() == "RUN":
						runStart = ts
						if runTimeIntervals == 0:
							opEvent.setActualProgress(0)
							runTimeIntervals +=1

					if opEvent.getOldStatus() == "RUN":
						runTimeIntervals +=1
						runEnd = ts
						if runStart!=None:
							diff = runEnd - runStart
							totalHours += float(diff/3600)
						else:
							runEnd = None

					opEvent.setActualHours(totalHours)
					#Update actualHours for the order ... 
					if orderN in orderList:
						for order_ts,order in orderList[orderN].items():
							if ts > order_ts:
								order.setActualHours(totalHours)

				opTotalHours[orderN][operationN] = totalHours
				opRunTimeIntervals[orderN][operationN] = runTimeIntervals

				orderTotalHours[orderN]+=totalHours
				orderPlannedHours[orderN]+=opEvent.getPlannedHours()

		#Set the actual total hour
		for orderN,_list in orderList.items():
			totalHours = orderTotalHours[orderN]
			plannedHours = orderPlannedHours[orderN]
			for ts,order in _list.items():
				order.setTotalHours(totalHours)
				order.setPlannedHours(plannedHours)

		#Create Sensor events
		for orderN in opEventList:
			for operationN in opEventList[orderN]:
				totalHours = opTotalHours[orderN][operationN]
				runTimeIntervals = opRunTimeIntervals[orderN][operationN]
				minEvent = 3
				if runTimeIntervals>0:
					eventsInterval = int(minEvent/runTimeIntervals)

					if eventsInterval < 1:
						eventsInterval = 1
					runStart = None

					for ts,opEvent in opEventList[orderN][operationN].items():

						opEvent.setTotalHours(totalHours)

						if opEvent.getNewStatus() == "RUN":
							runStart = ts
						if opEvent.getOldStatus() == "RUN":
							if runStart!=None:
								interval = (ts - runStart)
								if interval < 300:
									x = 1
								else:
									x = eventsInterval

								for i in range(0,x):
									i_aux = i+1
									x_aux = x+1
									timeShift = interval*(i_aux/x_aux)
									eventTS = (runStart + timeShift)
									while eventTS in eventDict:
										eventTS+=0.1
									if (eventTS < runStart) or (eventTS > ts):
										print("ERROR: evTS-start = " + str(eventTS - runStart) + "  end-evTS = " + str(ts-eventTS))
									hoursBefEvent = float((interval*(1-(i_aux/x_aux)))/3600)
									newSensorEvent = SensorEvent(opEvent,eventTS,(-hoursBefEvent),totalHours,runStart)
									eventDict.update({eventTS: newSensorEvent})
							else:
								runStart=None

	#eventDict = {**orderDict,**sensorEvents,**eventDict}

	#Sort all events by timestamps
	eventDict = dict(sorted(eventDict.items(), key=lambda item: item[0]))

	#Debug information
	numberOfEvents = len(eventDict)
	print("Total events: " + str(numberOfEvents))

	numberOfOrders = len(orderTotalHours)
	#numberOfOperations = 0
	operationsTotalHours = 0
	for operationList in opTotalHours.values():
		#numberOfOperations+=len(operationList)
		operationsTotalHours+=sum(operationList.values())

	return eventDict,numberOfOrders,numberOfOperations,operationsTotalHours,numberOfEvents

#check if the only orderEvent is a terminal status
#Remove completed orders or orders that have a
def checkOrderFirstStatus(orderList):
	for orderN in orderList:
		first_event = min(orderList[orderN])
		last_event = max(orderList[orderN])
		interval = last_event-first_event
		real_interval = orderList[orderN][last_event].getTimestamp() - orderList[orderN][first_event].getTimestamp() 
		print(str(real))
		if real_interval < 3600 or (orderList[orderN][first_event].getNewStatus() in ("CANCELLED","COMPLETE")):
			print("ORDER COMPLETE ..." + str(orderN))
			print("\n")
			for ts,order in orderList[orderN].items():
				print("\t" + str(ts) + " " + str(order.getNewStatus()))
			return False

	return True

#Checks the consistency of order events 
# ensure that there is at least one order event prior to the event of this operation
def checkPrevOrderEvents(op,orderList):
	op_ts = op.getTimestamp()
	priorOrderEvent = False
	if orderList==None:
		priorOrderEvent = False
	else:
		for timestamp in orderList.keys():
			if timestamp < op_ts:
				priorOrderEvent = True
				break
	
	order_ts=0
	newOrder=None

	if priorOrderEvent == False:
		#Create new orderEvent
		print("New Order: " + op.getOrderNumber())
		data = {}
		data.update({"ORDER_ID": op.getOrderNumber()})
		data.update({"NEW_STATUS": "-"})
		data.update({"OLD_STATUS": "-"})
		data.update({"SCHEDULE_START_DATE": " "})
		data.update({"PN": "-"})
		data.update({"ACTUAL_START_DATE": " "})
		data.update({"SITE": "-"})
		order_ts = datetime.fromtimestamp(op_ts-(24*3600))
		data.update({"STATUS_CHANGE_TS": datetime.strftime(order_ts, '%Y/%m/%d %H:%M:%S')})
		newOrder = Order(data)
		newOrder.setTotalHours(0)
		newOrder.setPlannedHours(0)
		order_ts = order_ts.timestamp()
			
	return order_ts,newOrder

def dropTable(cur,table):
	cur.execute("select exists(select * from information_schema.tables where table_name=%s)", (table,))
	if(cur.fetchone()[0]):
		cur.execute("DROP TABLE %s CASCADE;" % (table,))

def tabelExist(table):
	r = False
	with conn.cursor() as cur:
		cur.execute("select * from information_schema.tables where table_name=%s", (table,))
		r = bool(cur.rowcount)

	return r
# Insert WC, Parts - from csv files
def setDatabase():
	#Delete/Drop existing tables 
	with conn.cursor() as cur:
		dropTable(cur,'workcenter')
		#dropTable(cur,'part')
		dropTable(cur,'order_status_changes')
		dropTable(cur,'operation_status_changes')
		dropTable(cur,'sensor_events')
		dropTable(cur,'test_info')

		print("Drop tables ...")

		cur.execute(workcenter_table)
		print("Create WC table ...")

		#cur.execute(part_table)
		#print("Create Part table ...")

		#with open(part_file, 'r') as f:
		#	reader = csv.reader(f)
		#	next(reader) # Skip the header row.
		#	for row in reader:
		#		cur.execute(
		#			"INSERT INTO part VALUES (%s, %s, %s, %s, %s)",
		#			row
		#		)
		#	f.close()

		cur.execute(order_status_changes_table)
		print("Create Order table ...")
		cur.execute(orders_ended_function)
		cur.execute(orders_tot_function)

		cur.execute(operation_status_changes_table)
		print("Create Operation table ...")
		cur.execute(operations_tot_function)

		cur.execute(sensor_event_table)
		print("Create sensor_events table ...")

		cur.execute(test_info)
		print("Create test_info table ...")

	conn.commit()

orders_ended_function = """CREATE OR REPLACE FUNCTION public.orders_ended()
				    RETURNS SETOF character varying
				    LANGUAGE 'sql'
				    
				AS $BODY$
				SELECT orderNumber
				FROM order_status_changes
				WHERE ordernewstatus = 'COMPLETE' or ordernewstatus = 'CANCELLED'
				GROUP BY orderNumber
				$BODY$;
"""

operations_tot_function = """CREATE OR REPLACE FUNCTION public.tot_operations()
						    RETURNS bigint
						    LANGUAGE 'sql'
						    
						AS $BODY$
						SELECT count(operationnumber)
						FROM
							(SELECT ordernumber,operationnumber
							FROM operation_status_changes
							GROUP BY ordernumber,operationnumber) as foo;
$BODY$;
"""

orders_tot_function = """CREATE OR REPLACE FUNCTION public.tot_orders()
							    RETURNS bigint
							    LANGUAGE 'sql'
							    
							AS $BODY$
							SELECT count(ordernumber)
							FROM
								(SELECT ordernumber
								FROM order_status_changes
								GROUP BY ordernumber) as foo;
							$BODY$;
"""

workcenter_table = """	CREATE TABLE workcenter
					(
						denomination VARCHAR(75) NOT NULL,
						id INT GENERATED ALWAYS AS IDENTITY,
						PRIMARY KEY (id)
					);
					"""

#part_table = 	"""	CREATE TABLE part
#					(
#						partNumber VARCHAR(75) NOT NULL,
#						serialNumber VARCHAR(75) NOT NULL,
#						description VARCHAR(75) NOT NULL,
#						partRev VARCHAR(75) NOT NULL,
#						cemb VARCHAR(75) NOT NULL,
#						id INT GENERATED ALWAYS AS IDENTITY,
#						PRIMARY KEY (id)
#					);
#				"""

order_status_changes_table = 	"""	CREATE TABLE order_status_changes
									(
										orderNumber VARCHAR(45) NOT NULL,
										currentOperation INT,
										partNumber VARCHAR(45),
										orderNewStatus VARCHAR(20) NOT NULL,
										orderOldStatus VARCHAR(20) NOT NULL,
										plannedHours DECIMAL,
										currentHours DECIMAL,
										totalHours DECIMAL,
										scheduledStart TIMESTAMPTZ,
										scheduledEnd TIMESTAMPTZ,
										actualStart VARCHAR(20),
										actualEnd TIMESTAMPTZ,
										site VARCHAR(75),
										statusChangeTS TIMESTAMPTZ NOT NULL,
										updateTS TIMESTAMPTZ NOT NULL,
										id INT GENERATED ALWAYS AS IDENTITY,
										PRIMARY KEY (id)
									);
								"""

class Order():
	def __init__(self,row):
		self.orderNumber = row["ORDER_ID"]
		self.orderNewStatus = row["NEW_STATUS"]
		self.orderOldStatus = row["OLD_STATUS"]

		self.partNumber = row["PN"]

		if row["SCHEDULE_START_DATE"][0] != ' ':
			self.scheduledStartDate = row["SCHEDULE_START_DATE"]
		else:
			self.scheduledStartDate = None
		self.scheduledEndDate = None
		
		if row["ACTUAL_START_DATE"][0] != ' ':
			self.actualStart = row["ACTUAL_START_DATE"]
		else:
			self.actualStart = None

		self.actualEnd = None
		#self.part_id = self.getPartID()
		self.currentOperation = None
		self.plannedHours = 0
		self.site = row["SITE"]
		self.statusChangeTS = datetime.strptime(row["STATUS_CHANGE_TS"], '%Y/%m/%d %H:%M:%S').timestamp()
		self.actualHours = 0
		self.totalHours = 0
		self.updateTS = None

#	def getPartID(self):
#		with conn.cursor() as cur:
#			if self.partNumber!= None:
#				cur.execute("""SELECT id
#							FROM part
#							WHERE partnumber = %s; 
#						""",(self.partNumber,))
#
#			part_id = cur.fetchone()
#
#			if part_id != None:
#				self.part_id = part_id[0]
#			else:
#				self.part_id = 0 # NULL 

	def complete(self):
		return self.orderNewStatus == "COMPLETE"

	def getOrderNumber(self):
		return self.orderNumber

	def getTimestamp(self):
		return self.statusChangeTS

	def getNewStatus(self):
		return self.orderNewStatus

	def getOldStatus(self):
		return self.orderOldStatus

	def setTotalHours(self, totalHours):
		self.totalHours = totalHours

	def setPlannedHours(self, plannedHours):
		self.plannedHours = plannedHours

	def setActualHours(self, actualHours):
		self.actualHours = actualHours

	def setUpdateTS(self,timestamp):
		self.updateTS = timestamp

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
		print(str(datetime.fromtimestamp(self.statusChangeTS)) + " INSERT ORDER: " + self.orderNumber)
		with conn.cursor() as cur:
			cur.execute("""INSERT INTO order_status_changes VALUES 
					(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
					""",(self.orderNumber,self.currentOperation,self.partNumber,
						self.orderNewStatus,self.orderOldStatus,self.plannedHours,
						self.actualHours,self.totalHours,self.scheduledStartDate,
						self.scheduledEndDate,self.actualStart,self.actualEnd,self.site,
						datetime.fromtimestamp(self.statusChangeTS),
						datetime.fromtimestamp(self.updateTS)))

			conn.commit()
		return True


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
											plannedHours DECIMAL,
											actualHours DECIMAL,
											totalHours DECIMAL,
											statusChangeTS TIMESTAMPTZ NOT NULL,
											updateTS TIMESTAMPTZ NOT NULL,
											actualProgress DECIMAL,
											id INT GENERATED ALWAYS AS IDENTITY,
											PRIMARY KEY (id),
											CONSTRAINT fk_order FOREIGN KEY (order_id) REFERENCES order_status_changes(id),
											CONSTRAINT fk_workcenter FOREIGN KEY (workcenter_id) REFERENCES workcenter(id)
										);
									"""

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
				self.order_id = None

		opHours = row["PLANNED_DURATION"]
		if not(opHours.isdigit()):
			hours = opHours.split('-')
			size = len(hours)
			average = 0
			for h in hours:
				average = average + float(h)
			average = average/size
			opHours = average
		
		self.plannedHours = float(opHours)
		self.statusChangeTS = datetime.strptime(row["STATUS_CHANGE_TS"], '%Y/%m/%d %H:%M:%S').timestamp()
		self.updateTS = None

		self.actualProgress = None
		self.totalHours = 0

	def updateDates(self,first_event,start_day,scale):

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

	def getPlannedHours(self):
		return self.plannedHours

	def getActualHours(self):
		return self.actualHours

	def getTimestamp(self):
		return self.statusChangeTS

	def getTotalHours(self):
		return self.totalHours

	def setTotalHours(self, totalHours):
		self.totalHours = totalHours

	def setTimestamps(self, newTime):
		self.statusChangeTS = newTime

	def setStatus(self, newStatus):
		self.operationNewStatus = newStatus

	def setActualHours(self, hours):
		self.actualHours = hours

	def setActualProgress(self, progress):
		self.actualProgress = progress

	def getOldStatus(self):
		return self.operationOldStatus

	def getNewStatus(self):
		return self.operationNewStatus

	def update(self,attr,value):
		with conn.cursor() as cur:
			cur.execute("UPDATE operation_status_changes SET " + attr +  """= %s WHERE operation_id = %s;""",(value,self.operation_id,))
		conn.commit()

	def setUpdateTS(self,timestamp):
		if timestamp%1 == 0:
			self.updateTS=float(timestamp+0.01)
		else:
			self.updateTS = timestamp

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

			print(str(datetime.fromtimestamp(self.statusChangeTS)) + " INSERT OPERATION: " + str(self.order) + str(self.operation_id))

			with conn.cursor() as cur:
				cur.execute("""INSERT INTO operation_status_changes VALUES 
						(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
						""",(self.operation_id,self.workcenter,self.workcenter_id,
							self.order,self.order_id,self.description,
							self.operationNewStatus,self.operationOldStatus,
							self.plannedHours,self.actualHours,self.totalHours,
							datetime.fromtimestamp(self.statusChangeTS),
							datetime.fromtimestamp(self.updateTS),self.actualProgress))
			conn.commit()
			return True
		else:
			print("Failed to insert Operations: " + self.order + self.operation_id)

		return False

sensor_event_table = 	"""	CREATE TABLE sensor_events
							(
								workcenter_id INT NOT NULL,
								operationNumber VARCHAR(75) NOT NULL,
								orderNumber VARCHAR(75) NOT NULL,
								progress DECIMAL NOT NULL,
								timeStamp TIMESTAMPTZ NOT NULL,
								opRunStart TIMESTAMPTZ NOT NULL,
								updateTS TIMESTAMPTZ NOT NULL,
								id INT GENERATED ALWAYS AS IDENTITY,
								PRIMARY KEY (id)
							);
						"""

class SensorEvent():
	def __init__(self,opEvent,timestamp,hoursAftEvent,totalHours,opRunStart):
		self.workcenter=opEvent.getWorkCenterID()
		self.operationNumber=opEvent.getOperationNumber()
		self.orderNumber=opEvent.getOrderNumber()
		self.timestamp = int(timestamp)
		self.opRunStart = opRunStart

		opActualHours=opEvent.getActualHours()+hoursAftEvent
		opTotalHours=totalHours
		self.percentage = int((opActualHours/opTotalHours)*100)

		self.updateTS = None

	def setUpdateTS(self,timestamp):
		self.updateTS = timestamp

	def __str__(self):
		return ("SensorEvent: " + str(self.operationNumber) + " TimeStamp: " + str(self.timestamp) + " " + str(self.opRunStart) + " - - " + str(self.percentage) + "%")

	def updateDates(self,first_event,start_day,scale):
		if self.timestamp != None:
			timestamp = self.timestamp
			diff = timestamp - first_event.timestamp()
			sum_time = start_day.timestamp()+diff/scale
			self.timestamp = sum_time

	def getTimestamp(self):
		return self.timestamp

	def insert(self):

		print(str(datetime.fromtimestamp(self.timestamp)) + " INSERT EVENT: " + self.operationNumber)

		with conn.cursor() as cur:
			cur.execute("""INSERT INTO sensor_events VALUES (%s, %s, %s, %s, %s, %s, %s)""",
				(self.workcenter,self.operationNumber,self.orderNumber,self.percentage,
					datetime.fromtimestamp(self.timestamp),
					datetime.fromtimestamp(self.opRunStart),
					datetime.fromtimestamp(self.updateTS),))
		conn.commit()
		return True

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

#def readPart(known_Parts):
#	PartList = {}
#	with conn.cursor(cursor_factory=RealDictCursor) as cur:
#		if known_Parts != None:
#			cur.execute("SELECT * FROM part WHERE id NOT IN " + known_Parts + ";")
#		else:
#			cur.execute("SELECT * FROM part;")
#		data = cur.fetchall()
#
#		for part in data:
#			decode = json.dumps(part, indent=2, default=str)
#			encode = json.loads(decode)
#			PartList.update({encode["id"]: Entities.Part(encode)})
#
#	return PartList

def readNewOrders(knownOrders, time):
	OrderList = {}
	with conn.cursor(cursor_factory=RealDictCursor) as cur:

		query = " "

		if knownOrders != None:
			query =  " AND ordernumber NOT IN " + knownOrders

		cur.execute("""SELECT * FROM order_status_changes 
						WHERE updatets >= (NOW() - interval '""" + str(time) + """ seconds') 
						""" + query + 
						""" AND orderNumber NOT IN (SELECT orders_ended()) """ + 
						""" ORDER BY updatets desc;""")
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
				if OrderList[orderNumber].getTimestamp() < ord.getTimestamp():
					OrderList[orderNumber]=ord
			else:
				OrderList.update({orderNumber: ord})

	return OrderList

def readKnownOrders(knownOrders, time):
	OrderList = {}
	with conn.cursor(cursor_factory=RealDictCursor) as cur:

		if knownOrders != None:

			cur.execute("""SELECT * FROM order_status_changes 
							WHERE updatets >= (NOW() - interval '""" + str(time) + """ seconds') 
							AND ordernumber IN """ + knownOrders + """ 
							ORDER BY updatets desc;""")
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
					if OrderList[orderNumber].getTimestamp() < ord.getTimestamp():
						OrderList[orderNumber]=ord
				else:
					OrderList.update({orderNumber: ord})

	return OrderList

# Completed or canceled operations are ignored
def readNewOperation(orderNumber, known_Operations, knownEnded_Operations, time):
	OperationList = {}
	with conn.cursor(cursor_factory=RealDictCursor) as cur:

		query = " "

		known_Ops = None
		if(orderNumber in known_Operations):
			known_Ops = known_Operations[orderNumber]
			query = " AND operationnumber NOT IN " + known_Ops

		knownEnded_Ops = None
		if orderNumber in knownEnded_Operations:
			knownEnded_Ops = knownEnded_Operations[orderNumber]
			query = query + " AND operationnumber NOT IN " + knownEnded_Ops

		cur.execute("""SELECT * FROM operation_status_changes 
						WHERE updatets >= (NOW() - interval '""" + str(time) + """ seconds') 
						AND (ordernumber = '""" + str(orderNumber) + """'""" + query + """) 
						ORDER BY updatets desc;""")
		data = cur.fetchall()

		for operation in data:
			decode = json.dumps(operation, indent=2, default=str)
			encode = json.loads(decode)
			op = Entities.Operation()
			op.loadDBEntry(encode)

			operationNumber = op.getOperationID()

			#Get only the last update/statusChanges Or get all the updates and insert the updates in order ???
			if operationNumber in OperationList:
				if OperationList[operationNumber].getTimestamp() < op.getTimestamp():
					OperationList[operationNumber] = op
			else:
				OperationList.update({operationNumber: op})

	return OperationList

def readKnownOperations(orderNumber, known_Operations, time):
	OperationList = {}
	with conn.cursor(cursor_factory=RealDictCursor) as cur:

		query = " "

		known_Ops = None
		if(orderNumber in known_Operations):
			known_Ops = known_Operations[orderNumber]
			query = " AND operationnumber IN " + known_Ops

		cur.execute("""SELECT * FROM operation_status_changes 
						WHERE updatets >= (NOW() - interval '""" + str(time) + """ seconds') 
						""" + query + """ 
						AND ordernumber = '""" + str(orderNumber) + """' 
						ORDER BY updatets desc;""")

		data = cur.fetchall()

		for operation in data:
			decode = json.dumps(operation, indent=2, default=str)
			encode = json.loads(decode)
			op = Entities.Operation()
			op.loadDBEntry(encode)

			operationNumber = op.getOperationID()

			#Get only the last update/statusChanges Or get all the updates and insert the updates in order ???
			if operationNumber in OperationList:
				if OperationList[operationNumber].getTimestamp() < op.getTimestamp():
					OperationList[operationNumber] = op
			else:
				OperationList.update({operationNumber: op})

	return OperationList

def readNewSensorEvents(lastID, time):

	protocol = "PDI-IoTA-UltraLight"
	apikey = "hfe9iuh83qw9hr8ew9her9"
	ref = "/iot/d"

	SensorEvList = {}
	with conn.cursor(cursor_factory=RealDictCursor) as cur:
		cur.execute("""SELECT * FROM sensor_events 
						WHERE updatets >= (NOW() - interval '""" + str(time) + """ seconds') AND
						id > """ + str(lastID) + """ ORDER BY updatets;""")
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

test_info = """ CREATE TABLE test_info
				(
					actualStart TIMESTAMPTZ NOT NULL,
					actualEnd TIMESTAMPTZ NOT NULL,
					virtualStart TIMESTAMPTZ NOT NULL,
					virtualEnd TIMESTAMPTZ NOT NULL,
					numberOfOrders DECIMAL NOT NULL,
					numberOfOperations DECIMAL NOT NULL,
					operationsTotalHours DECIMAL NOT NULL,
					numberOfEvents DECIMAL,
					id INT GENERATED ALWAYS AS IDENTITY,
					PRIMARY KEY (id)
				)
			"""

class TestInfo():
	def __init__(self,actualStart,actualEnd,virtualStart,virtualEnd,numberOfOrders,numberOfOperations,operationsTotalHours,numberOfEvents):
		self.actualStart=datetime.fromtimestamp(int(actualStart))
		self.actualEnd=datetime.fromtimestamp(int(actualEnd))
		self.virtualStart=datetime.fromtimestamp(int(virtualStart))
		self.virtualEnd=datetime.fromtimestamp(int(virtualEnd))
		self.numberOfOrders=numberOfOrders
		self.numberOfOperations=numberOfOperations
		self.numberOfEvents=numberOfEvents
		self.operationsTotalHours=operationsTotalHours

	def insert(self):

		with conn.cursor() as cur:
			cur.execute("""INSERT INTO test_info VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
				(self.actualStart,self.actualEnd,self.virtualStart,self.virtualEnd,
					self.numberOfOrders,self.numberOfOperations,self.operationsTotalHours,
					self.numberOfEvents))
		conn.commit()
		return True

#Debug info
def readTestInfo():

	info = None
	with conn.cursor(cursor_factory=RealDictCursor) as cur:
		cur.execute("""SELECT * FROM test_info LIMIT 1""")
		data = cur.fetchall()

		if len(data) > 0:
			decode = json.dumps(data[0], indent=2, default=str)
			encode = json.loads(decode)
			print(encode)
			info = Entities.TestInfo(encode)

	return info