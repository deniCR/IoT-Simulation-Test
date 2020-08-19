#!/usr/bin/env python3

from time import sleep

import Classes.Entities as Entities
import Classes.DB_Entities as DB_Entities

def merge_two_dicts(x, y):
	z = x.copy()   # start with x's keys and values
	z.update(y)    # modifies z with y's keys and values & returns None
	return z

def main():
	stop = False

	newWorkCenterList = DB_Entities.readWorkCenter()
	for wc in newWorkCenterList.values():
		wc.provision()
		del wc

	del newWorkCenterList

	newPartList = DB_Entities.readPart()
	for part in newPartList.values():
		part.provision()
		del part

	del newPartList

	#newOperationList = readOperation()
	#for op in newOperationList.values():
	#	op.provision()
	#	del op

	#del newOperationList

	while not(stop):
		sleep(1)
		known_ordersList, known_Orders = Entities.getRunningOrders()
		operationList, known_Operations = Entities.getRunningOperations()

		newList = DB_Entities.readNewOrders(known_Orders)

		for orderNumber, order in newList.items():
			opList = DB_Entities.readNewOperation(orderNumber, known_Operations)
			for op in opList.values():
				op.provision()
			order.provision()

		updateList = None
		if known_Orders != None:
			updateList = DB_Entities.collectKnownOrders(known_Orders)

			for orderNumber, order in updateList.items():
				if orderNumber in known_ordersList and order.compareTimeStams(known_ordersList[orderNumber]):
					print("Compara order: " + " " + order.getID() + " " + order.getOrderNumber() + " " + order.getTimeStamp() + " vs " + " " + known_ordersList[orderNumber].getID() + " " + known_ordersList[orderNumber].getOrderNumber() + " " + known_ordersList[orderNumber].getTimeStamp())
					order.update()
					if order.getOrderID() != order.getOrderNumber():
						exit()
					opList = DB_Entities.collectKnownOperations(orderNumber, known_Operations)
					for opN, op in opList.items():
						if operationList != None and (opN in operationList and (op.getTimeStamp() > op.getTimeStamp())):
							print("\tCompara operation: " + " " + op.getID() + " " + op.getOperationNumber() + " " + op.getTimeStamp() + " vs " + " " + known_Operations[opN].getID() + " " + known_Operations[opN].getOperationNumber() + " " + known_Operations[opN].getTimeStamp())
							op.update()
							if op.getOperationID() != op.getOperationNumber():
								exit()

		del known_ordersList
		known_ordersList = None
		del newList
		newList = None
		del updateList
		updateList = None
		del operationList
		operationList = None
		del known_Orders
		known_Orders = None
		del known_Operations
		known_Operations = None

if __name__ == "__main__":
		main()