import requests
import json
from time import sleep
import threading
import random

host = "http://192.168.0.108"
iot_agent = host + ":4041/iot"
agent_reciver = host + ":7896/iot"
iot_headers = {
	'fiware-service': 'openiot',
	'fiware-servicepath': '/',
	'Content-Type': 'application/json'
}
ul_headers = {
	'Content-Type': 'text/plain'
}

def post(url,headers,payload):
	try:
		response = requests.request("POST", url, headers=headers, data = payload)
		#response.raise_for_status()
		#print(response.text.encode('utf8'))
	except requests.exceptions.HTTPError as errh:
			print ("Http Error:",errh)
	except requests.exceptions.ConnectionError as errc:
			print ("Error Connecting:",errc)
	except requests.exceptions.Timeout as errt:
			print ("Timeout Error:",errt)
	except requests.exceptions.RequestException as err:
			print ("OOps: Something Else",err)

class Service:
	def __init__(self, cbroker, apikey, entity_type, resource):
		self.cbroker = cbroker
		self.apikey = apikey
		self.entity_type = entity_type
		self.resource = resource
		self.agent_url = iot_agent + "/services"
		self.payload = {
				 "services": [
					 {
						 "apikey":      self.apikey,
						 "cbroker":     self.cbroker,
						 "entity_type": self.entity_type,
						 "resource":    self.resource
					 }
				 ]
		}

	def provision(self):
		url = self.agent_url
		post(url,iot_headers,json.dumps(self.payload))

class Device:
	def __init__(self, id, type, name, protocol, apikey):
		self.device_id = id
		self.entity_type = type
		self.entity_name = "urn:ngsi-ld:" + name
		self.protocol = protocol
		self.agent_url = iot_agent + "/devices"
		self.apikey = apikey
		self.payload = {
			 "devices": [
				 {
					 "device_id":   self.device_id,
					 "entity_name": self.entity_name,
					 "entity_type": self.entity_type,
					 "protocol":    self.protocol,
				}
				]
			}

	#def add_properties(self):

	def send_data(self):
		url=agent_reciver+"/d?k="+self.apikey+"&i="+self.device_id
		data = random.random()*100
		payload="t|"+str(data)
		post(url,ul_headers,payload)


	def provision(self):
		url = self.agent_url
		post(url,iot_headers,json.dumps(self.payload))

class TempSensor(Device):
	def __init__(self, id, protocol, apikey, ref):
		super().__init__("temperatureSensor"+str(id), "TemperatureSensor", "TemperatureSensor:"+str(id), protocol, apikey)
		self.ref = ref
		self.payload = {
			 "devices": [
				 {
					 "device_id":   self.device_id,
					 "entity_name": self.entity_name,
					 "entity_type": self.entity_type,
					 "protocol":    self.protocol,
					 "attributes": [
							{ "object_id": "t", "name": "temperature", "type": "Float" }
						],
						"static_attributes": [
							{ "name":"refStore", "type": "Relationship", "value": self.ref}
						]
				}
				]
			}

class HumSensor(Device):
	def __init__(self, id, protocol, apikey, ref):
		super().__init__("humiditySensor"+str(id), "HumiditySensor", "HumiditySensor:"+str(id), protocol, apikey)
		self.ref = ref
		self.payload = {
			 "devices": [
				 {
					 "device_id":   self.device_id,
					 "entity_name": self.entity_name,
					 "entity_type": self.entity_type,
					 "protocol":    self.protocol,
					 "attributes": [
							{ "object_id": "h", "name": "humidity", "type": "Float" }
						],
						"static_attributes": [
							{ "name":"refStore", "type": "Relationship", "value": self.ref}
						]
				}
				]
			}

class LightSensor(Device):
	def __init__(self, id, protocol, apikey, ref):
		super().__init__("lightSensor"+str(id), "LightSensor", "LightSensor:"+str(id), protocol, apikey)
		self.ref = ref
		self.payload = {
			 "devices": [
				 {
					 "device_id":   self.device_id,
					 "entity_name": self.entity_name,
					 "entity_type": self.entity_type,
					 "protocol":    self.protocol,
					 "attributes": [
							{ "object_id": "l", "name": "Light", "type": "Integer" }
						],
						"static_attributes": [
							{ "name":"refStore", "type": "Relationship", "value": self.ref}
						]
				}
				]
			}

class CO2Sensor(Device):
	def __init__(self, id, protocol, apikey, ref):
		super().__init__("co2sensor"+str(id), "CO2Sensor", "CO2Sensor:"+str(id), protocol, apikey)
		self.ref = ref
		self.payload = {
			 "devices": [
				 {
					 "device_id":   self.device_id,
					 "entity_name": self.entity_name,
					 "entity_type": self.entity_type,
					 "protocol":    self.protocol,
					 "attributes": [
							{ "object_id": "c", "name": "CO2", "type": "Integer" }
						],
						"static_attributes": [
							{ "name":"refStore", "type": "Relationship", "value": self.ref}
						]
				}
				]
			}

def simulate_device(device, samples, stop):
	sleeptime = float(1.0/samples)
	print(sleeptime)

	i=0
	while True:
		device.send_data()
		if stop():
			break
		print(i)
		i+=1
		sleep(sleeptime)
		pass

def read_conf_file(file):
	run_time = 0
	service = Service("http://orion:1026","4jggokgpepnvsb2uv4s40d59ov","Devices","/iot/d")
	apikey = service.apikey
	devices = []
	sample = []
	t=0;h=0;l=0;c=0

	with open(file) as file_object:
		line = file_object.readline()
		while line:
			x = line.split()
			key = x[0]

			if key == 'run_time':
				run_time = int(x[1])

			if key == 'service':
				service = Service(x[1],x[2],x[3],x[4])
				apikey = x[2]

			if key == 'device':
				type = x[1]
				if type == 't':
					devices.append(TempSensor(t,x[2],apikey,x[3]))
					t+=1
				if type == 'h':
					devices.append(HumSensor(h,x[2],apikey,x[3]))
					h+=1
				if type == 'l':
					devices.append(LightSensor(l,x[2],apikey,x[3]))
					l+=1
				if type == 'c':
					devices.append(TempSensor(t,x[2],apikey,x[3]))
					t+=1
				sample.append(int(x[5]))

			line = file_object.readline()


	return run_time,service,devices,sample


def main():
	run_time=0
	#read from confg file ...
	run_time,service,devices,sample=read_conf_file('DummyDevices.conf')


	#service = Service("http://orion:1026","4jggokgpepnvsb2uv4s40d59ov","Devices","/iot/d")
	service.provision()
	#devices.append(Device("temperatureSensor007","TemperatureSensor","urn:ngsi-ld:TemperatureSensor:007","PDI-IoTA-UltraLight","4jggokgpepnvsb2uv4s40d59ov"))
	#devices[0].provision()
	
	stop_threads = False
	threads = []
	
	i=0
	for d in devices:
		d.provision()
		threads.append(threading.Thread(target=simulate_device,args=(d,sample[i],lambda : stop_threads,)))
		i+=1
		pass

	for t in threads:
		t.start()
		pass

	#The threads will run until the time is completed...
	sleep(run_time)
	stop_threads=True

	for t in threads:
		t.join()
		pass

if __name__ == "__main__":
		main()


