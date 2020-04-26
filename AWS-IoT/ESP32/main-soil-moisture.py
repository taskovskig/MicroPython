import time
import json
import esp32
import sys
import machine
from machine import Pin, ADC
from network import WLAN
import network
from umqtt.robust import MQTTClient

### Settings
WLAN_ESSID = "WLAN_AP"
WLAN_PASSWORD = "AP_PASSWORD"
IOT_ENDPOINT = "xxxxxxxxxxxxxx-ats.iot.eu-central-1.amazonaws.com"
THING = "ESP32-WROOM-32D-IOT-2"
TOPIC = "things/measurements"
THING_SHADOW = "$aws/things/" + THING + "/shadow/update"
KEY_PATH = "/32-02.key.der"
CERT_PATH = "/32-02.cert.der"
IDLE_TIME = 55
PVT_KEY = None
CERT_KEY = None

### Initial setup
wlan = network.WLAN(network.STA_IF)
ADC.width(ADC.WIDTH_12BIT)
pot = ADC(Pin(34))
pot.atten(ADC.ATTN_11DB)

# Load certificate and key
with open(KEY_PATH, 'rb') as f:
	PVT_KEY = f.read()
with open(CERT_PATH, 'rb') as f:
	CERT_KEY = f.read()

### Functions
# Device idle
def deviceIdle(t):
	time.sleep(t)

# WiFi connect
def connectToWiFi(retries_limit):
	print('WiFi Setup...')
	if not wlan.isconnected():
		retries = 0
		wlan.active(True)
		wlan.connect(WLAN_ESSID, WLAN_PASSWORD)
		while not wlan.isconnected():
			time.sleep_ms(500)
			retries = retries + 1
			print('.', end=' ')
			if retries == retries_limit:
				count = 0
				while count < 10:
					time.sleep_ms(500)
					count = count + 1
				machine.reset()
	if wlan.isconnected():
		print('WiFi Connected')

def soilMoistureMeas():
	r = {}
	try:
		pot_value = pot.read()
		print("Soil Moisture: " + str(pot_value))
		soil_moisture = round(100 * (4095 - pot_value) / 4095, 2)
		r = {
			'status': 'OK',
			'soilMoisture': soil_moisture
		}
	except:
		r = {
			'status': 'NOK'
		}
	return r

# MQTT publish
def publishMQTT(sm):
	message = {
		"state": {
			"reported": {
				"thing": THING,
				"soilMoisture": sm["soilMoisture"]
			}
		}
	}
	print(message)
	mqtt.publish(
		topic = TOPIC,
		msg = json.dumps(message),
		qos = 0
	)
	message['state']['reported']['connected'] = True
	mqtt.publish(
		topic = THING_SHADOW,
		msg = json.dumps(message),
		qos = 0
	)

# Connect to MQTT broker
mqtt = MQTTClient(
	THING,
	IOT_ENDPOINT,
	port = 8883,
	keepalive = 10000,
	ssl = True,
	ssl_params = {
		"cert": CERT_KEY,
		"key": PVT_KEY,
		"server_side": False
	}
)

connectToWiFi(20)
try:
	mqtt.connect()
except:
	machine.reset()

# Publish measurements
while True:
	if not wlan.isconnected():
		connectToWiFi(20)
	try:
		r = soilMoistureMeas()
		print(r)
		if r["status"] == "OK":
			publishMQTT(r)
		print()
		deviceIdle(IDLE_TIME)
	except:
		machine.reset()

# Disconnect
#mqtt.disconnect()
sys.exit()
