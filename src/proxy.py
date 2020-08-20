#!/usr/bin/env python3

from time import sleep

import Classes.Entities as Entities
import Classes.DB_Entities as DB_Entities

def collectNewEvents(known_Orders, known_Operations):
	newList = DB_Entities.readNewOrders(known_Orders)

	for orderNumber, order in newList.items():
		opList = DB_Entities.readNewOperation(orderNumber, known_Operations)
		for op in opList.values():
			op.provision()
		order.provision()

def updateKnownEntities(known_Orders, known_ordersList, known_Operations, known_operationList):
	updateList = DB_Entities.collectKnownOrders(known_Orders)

	for orderNumber, order in updateList.items():
		if orderNumber in known_ordersList and order.compareTimeStams(known_ordersList[orderNumber]):
			order.update()
			opList = DB_Entities.collectKnownOperations(orderNumber, known_Operations)
			for opN, op in opList.items():
				if known_operationList != None and (opN in known_operationList and (op.getTimeStamp() > op.getTimeStamp())):
					op.update()

def main():
	stop = False

	while not(stop):
		sleep(1)

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

		#GET Known Orders and Operations from the broker

		known_ordersList, known_Orders = Entities.getRunningOrders()
		known_operationList, known_Operations = Entities.getRunningOperations()

		collectNewEvents(known_Orders, known_Operations)
		updateKnownEntities(known_Orders, known_ordersList, known_Operations, known_operationList)

if __name__ == "__main__":
		main()