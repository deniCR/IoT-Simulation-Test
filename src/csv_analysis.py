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
	totals = {}
	total_ttt = 0
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

				if not (old_status in totals):
					totals.update({old_status: 0 })

				if not (old_status in eventDict[order_id]): 
					eventDict[order_id].update({old_status: {} })
					eventDict[order_id][old_status].update({total_t: 0 })

				if not (new_status in eventDict[order_id][old_status]):
					eventDict[order_id][old_status].update({new_status: 0 })

				total_ttt = total_ttt + 1
				total_tt_value = totals[old_status] + 1
				total_t_value = eventDict[order_id][old_status][total_t] + 1
				old_value = eventDict[order_id][old_status][new_status] + 1

				totals[old_status] = total_tt_value
				eventDict[order_id][old_status].update({new_status: old_value })
				eventDict[order_id][old_status].update({total_t: total_t_value })

	total = {}
	total.update({"300": 0})
	total.update({"700": 0})

	for order in eventDict:
		print(order)
		for old_st in eventDict[order]:
			total_tt = totals[old_st]
			total_t = eventDict[order][old_st]["total_t"]
			print(old_st)
			for new_st in eventDict[order][old_st]:
				total[order] = total[order] + 100*(eventDict[order][old_st][new_st]/total_ttt/2)

				print(new_st,eventDict[order][old_st][new_st],100*(eventDict[order][old_st][new_st]/total_t))
			print("---------------------------------------------")
		print("+++++++++++++++++++++++++++++++++++++++++++++")

	for order in total:
		print(total[order])

# Read csv files
def process(orders,operations):
	eventDict = {}
	with open(operations, mode='r') as csv_file:
		order_dict = csv.DictReader(csv_file)

		planedHours = "planedHours"
		numberOfOperations = "numberOfOperations"

		for row in order_dict:

			operation_id = row["OPER_ID"]
			order_id = row["ORDER_ID"]

			opHours = row["PLANNED_DURATION"]

			if not(opHours.isdigit()):
				hours = opHours.split('-')
				size = len(hours)
				average = 0
				for h in hours:
					hh = float(h)
					#Há valores superiores a 30h que não devem ser considerados para o caso de testes ...
					if hh < 30:
						average = average + hh
					else:
						size = size-1

				average = average/size
				opHours = average

			if not (order_id in eventDict):
				eventDict.update({order_id: {} })
				eventDict[order_id].update({numberOfOperations: 0 })
				eventDict[order_id].update({planedHours: 0.0 })

			if not (operation_id in eventDict[order_id]):
				eventDict[order_id].update({operation_id: [] })
				eventDict[order_id][numberOfOperations] = eventDict[order_id][numberOfOperations] +1
				eventDict[order_id][planedHours] = eventDict[order_id][planedHours] + float(opHours)

				eventDict[order_id][operation_id].append(row)

	print("\"ORDER_ID\",\"PN\",\"SCHEDULE_START_DATE\",\"ACTUAL_START_DATE\",\"PLANNED_DURATION\",\"SITE\",\"STATUS_CHANGE_TS\",\"OLD_STATUS\",\"NEW_STATUS\",\"TOTAL_HOURS\",\"TOTAL_OPS\"")

	with open(orders, mode='r') as csv_file:
		order_dict = csv.DictReader(csv_file)

		planedHours = "planedHours"
		numberOfOperations = "numberOfOperations"

		for row in order_dict:

			order_id = row["ORDER_ID"]
			pn = row["PN"]
			sc_start = row["SCHEDULE_START_DATE"]
			ac_start = row["ACTUAL_START_DATE"]
			pl_d = row["PLANNED_DURATION"]
			site = row["SITE"]
			st_changes = row["STATUS_CHANGE_TS"]
			old_st = row["OLD_STATUS"]
			new_st = row["NEW_STATUS"]

			if order_id in eventDict:
				print("\"" + order_id + "\",\"" + pn  + "\",\"" + sc_start + "\",\"" + ac_start + "\",\"" + pl_d + "\",\"" + site + "\",\"" + st_changes + "\",\"" + old_st + "\",\"" + new_st + "\",\"" +  "{:.2f}".format(eventDict[order_id][planedHours]) + "\",\"" + str(eventDict[order_id][numberOfOperations]) + "\"")


def main():
	readCSV("csv_file/Order.csv")
	print("##############################")
	readCSV_percentagem("csv_file/Order.csv")

	#process("csv_file/Order.csv","csv_file/operations_change_status_alt_7")

if __name__ == "__main__":
		main()