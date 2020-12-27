#!/usr/bin/env python3

import signal
import os
from time import sleep

import Classes.Entities as Entities
import Classes.DB_Entities as DB_Entities

stop = False

def signal_handler(sig, frame):
	global stop
	stop = True

signal.signal(signal.SIGINT, signal_handler)

def readNewEvents(known_ordersList, known_OrdersIDs, known_OperationsIDs, knownEnded_OperationsIDs, time):
	newList = DB_Entities.readNewOrders(known_OrdersIDs, time)

	orderProvioned = 0
	operationsProvisioned = 0

	for orderNumber, order in newList.items():
		opList = DB_Entities.readNewOperation(orderNumber, known_OperationsIDs, knownEnded_OperationsIDs, time)
		for op in opList.values():
			op.provision()
			operationsProvisioned = operationsProvisioned +1
		order.provision()
		orderProvioned = orderProvioned +1

	for orderNumber in known_ordersList.keys():
		opList = DB_Entities.readNewOperation(orderNumber, known_OperationsIDs, knownEnded_OperationsIDs, time)
		for op in opList.values():
			op.provision()
			operationsProvisioned = operationsProvisioned +1

	return orderProvioned,operationsProvisioned

def updateKnownEntities(known_OrdersIDs, known_ordersList, known_OperationsIDs, known_operationList, time):
	updateList = DB_Entities.readKnownOrders(known_OrdersIDs, time)

	orderUpdated = 0
	operationsUpdated = 0

	for orderNumber, order in known_ordersList.items():
		if orderNumber in updateList and updateList[orderNumber].compareTimeStams(order):
			updateList[orderNumber].update()
			orderUpdated = orderUpdated +1

		opList = DB_Entities.readKnownOperations(orderNumber, known_OperationsIDs, time)
		for opN, op in opList.items():
			if (orderNumber in known_operationList) and known_operationList[orderNumber] != None and (opN in known_operationList[orderNumber] and (op.compareTimeStams(known_operationList[orderNumber][opN]))):
				op.update()
				print("Update operation: " + opN)
				operationsUpdated = operationsUpdated +1

	return orderUpdated,operationsUpdated

def main():
	global stop

	orderProvioned = 0
	operationsProvisioned = 0
	orderUpdated = 0
	operationsUpdated = 0

	#Debug
	test_info = None
	while test_info == None:
		sleep(1)
		test_info = DB_Entities.readTestInfo()
	test_info.provision()

	while not(stop):
		sleep(0.03)
		#GET Known work centers from the broker
		# - There are no updates to this entities ...
		known_WorkCenters = Entities.getWorkCenters()

		newWorkCenterList = DB_Entities.readWorkCenter(known_WorkCenters)
		for wc in newWorkCenterList.values():
			wc.provision()
			del wc

		#GET Known parts from the broker
		# - There are no updates to this entities ...
		known_Parts = Entities.getParts()

		newPartList = DB_Entities.readPart(known_Parts)
		for part in newPartList.values():
			part.provision()
			del part

		#time = 300 #Events from the last T seconds in real time (last ~5min)

		time = int(12*3600/float(os.environ['TIME_SCALE'])) # 12h of virtual time

		#GET Known Orders and Operations from the broker
		known_ordersList, known_OrdersIDs = Entities.getRunningOrders()
		known_operationList, known_OperationsIDs = Entities.getRunningOperations()
		knownEnded_operationList, knownEnded_OperationsIDs = Entities.getEndedOperations()

		aux_orderProvioned,aux_operationsProvisioned = readNewEvents(known_ordersList,known_OrdersIDs, known_OperationsIDs, knownEnded_OperationsIDs, time)
		aux_orderUpdated,aux_operationsUpdated = updateKnownEntities(known_OrdersIDs, known_ordersList, known_OperationsIDs, known_operationList, time)

		orderProvioned = orderProvioned + aux_orderProvioned
		operationsProvisioned = operationsProvisioned + aux_operationsProvisioned
		orderUpdated = orderUpdated + aux_orderUpdated
		operationsUpdated = operationsUpdated + aux_operationsUpdated

	print("Order Provision: " + str(orderProvioned))
	print("Operation Provision: " + str(operationsProvisioned))
	print("Order updated: " + str(orderUpdated))
	print("Operation updated: " + str(operationsUpdated))
	print("\n\n")

if __name__ == "__main__":
		main()
