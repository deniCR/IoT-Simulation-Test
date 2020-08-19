#!/usr/bin/env python3

import csv

# Read csv files
def readCSV(operation):
	eventDict = {}
	with open(operation, mode='r') as csv_file:
		operation_dict = csv.DictReader(csv_file)
		for row in operation_dict:

			old_status = row["OLD_STATUS"]
			new_status = row["NEW_STATUS"]
			order_id = row["ORDER_ID"][0:3]
			casos = "casos"

			if order_id == '300' or order_id == '700':
				if not (order_id in eventDict):
					eventDict.update({order_id: {} })
					eventDict[order_id].update({casos: 0 })

				if not (old_status in eventDict[order_id]): 
					eventDict[order_id].update({old_status: {} })

				if not (new_status in eventDict[order_id][old_status]):
					eventDict[order_id][old_status].update({new_status: 0 })

				old_value = eventDict[order_id][old_status][new_status]
				total_casos = eventDict[order_id][casos]
				eventDict[order_id][old_status].update({new_status: old_value+1 })
				eventDict[order_id].update({casos:  total_casos+1 })

	for order in eventDict:
		total_casos = eventDict[order][casos]
		print(order)
		for old_st in eventDict[order]:
			if old_st != "casos":
				print(old_st)
				for new_st in eventDict[order][old_st]:
					print(new_st,eventDict[order][old_st][new_st],eventDict[order][old_st][new_st]/total_casos)
				print("---------------------------------------------")
		print("+++++++++++++++++++++++++++++++++++++++++++++")

# Read csv files
def readCSV_percentagem(operation):
	eventDict = {}
	with open(operation, mode='r') as csv_file:
		operation_dict = csv.DictReader(csv_file)
		for row in operation_dict:

			old_status = row["OLD_STATUS"]
			new_status = row["NEW_STATUS"]
			order_id = row["ORDER_ID"][0:3]
			total_t = "total_t"

			if order_id == '300' or order_id == '700':
				if not (order_id in eventDict):
					eventDict.update({order_id: {} })

				if not (old_status in eventDict[order_id]): 
					eventDict[order_id].update({old_status: {} })
					eventDict[order_id][old_status].update({total_t: 0 })

				if not (new_status in eventDict[order_id][old_status]):
					eventDict[order_id][old_status].update({new_status: 0 })

				total_t_value = eventDict[order_id][old_status][total_t] + 1
				old_value = eventDict[order_id][old_status][new_status] + 1

				eventDict[order_id][old_status].update({new_status: old_value })
				eventDict[order_id][old_status].update({total_t: total_t_value })

	for order in eventDict:
		print(order)
		for old_st in eventDict[order]:
			total_t = eventDict[order][old_st]["total_t"]
			print(old_st)
			for new_st in eventDict[order][old_st]:
				print(new_st,eventDict[order][old_st][new_st],eventDict[order][old_st][new_st]/total_t)
			print("---------------------------------------------")
		print("+++++++++++++++++++++++++++++++++++++++++++++")


readCSV("operations_change_status_3")
print("##############################")
readCSV_percentagem("operations_change_status_3")


