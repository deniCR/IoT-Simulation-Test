#!/usr/bin/env python3

import signal

import Classes.Entities as Entities
import Classes.DB_Entities as DB_Entities

stop = False

def signal_handler(sig, frame):
    global stop
    stop = True
signal.signal(signal.SIGINT, signal_handler)

def collectNewEvents(known_Orders, known_Operations, time):
	newList = DB_Entities.readNewOrders(known_Orders, time)

	orderProvioned = 0
	operationsProvisioned = 0

	for orderNumber, order in newList.items():
		opList = DB_Entities.readNewOperation(orderNumber, known_Operations, time)
		for op in opList.values():
			op.provision()
			operationsProvisioned = operationsProvisioned +1
		order.provision()
		orderProvioned = orderProvioned +1

	return orderProvioned,operationsProvisioned

def updateKnownEntities(known_Orders, known_ordersList, known_Operations, known_operationList, time):
	updateList = DB_Entities.collectKnownOrders(known_Orders, time)

	orderUpdated = 0
	operationsUpdated = 0

	for orderNumber, order in updateList.items():
		if orderNumber in known_ordersList and order.compareTimeStams(known_ordersList[orderNumber]):
			order.update()
			orderUpdated = orderUpdated +1

			opList = DB_Entities.collectKnownOperations(orderNumber, known_Operations, time)
			for opN, op in opList.items():
				if orderNumber in known_operationList and known_operationList[orderNumber] != None and (opN in known_operationList[orderNumber] and (op.compareTimeStams(known_operationList[orderNumber][opN]))):
					op.update()
					print("Update operation: " + opN)
					operationsUpdated = operationsUpdated +1

	return orderUpdated,operationsUpdated

def main():

	orderProvioned = 0
	operationsProvisioned = 0
	orderUpdated = 0
	operationsUpdated = 0

	while not(stop):

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

		time = 1 #Events from the last 5 minutes

		#GET Known Orders and Operations from the broker
		known_ordersList, known_Orders = Entities.getRunningOrders()
		known_operationList, known_Operations = Entities.getRunningOperations()

		aux_orderProvioned,aux_operationsProvisioned = collectNewEvents(known_Orders, known_Operations, time)
		aux_orderUpdated,aux_operationsUpdated = updateKnownEntities(known_Orders, known_ordersList, known_Operations, known_operationList, time)

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
