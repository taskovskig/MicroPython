import time
import sys
import json
import machine
from machine import Pin, ADC
from network import WLAN
import network
from umqtt.simple import MQTTClient

led = Pin(2, Pin.OUT, value=1)

### Settings
WLAN_ESSID = "WLAN_AP"
WLAN_PASSWORD = "AP_PASSWORD"
IOT_ENDPOINT = "xxxxxxxxxxxxxx-ats.iot.eu-central-1.amazonaws.com"
THING = "ESP8266-NODEMCU-V3-IOT-5 (YOUR THING ID)"
TOPIC = "things/measurements"
THING_SHADOW = "$aws/things/" + THING + "/shadow/update"
KEY_PATH = "/8266-05.key.der"
CERT_PATH = "/8266-05.cert.der"
IDLE_TIME = 45
PVT_KEY = None
CERT_KEY = None

### Initial setup
# Set leds and pins
wlan = network.WLAN(network.STA_IF)
pot = ADC(0)

# Load certificate and key
with open(KEY_PATH, 'rb') as f:
	PVT_KEY = f.read()
with open(CERT_PATH, 'rb') as f:
	CERT_KEY = f.read()

### Functions
# Device idle
def deviceIdle(t):
	time.sleep(10)
	led.value(1)
	time.sleep(t)

# WiFi connect
def connectToWiFi(retries_limit):
	state = 1
	print('WiFi Setup...')
	if not wlan.isconnected():
		retries = 0
		wlan.active(True)
		wlan.connect(WLAN_ESSID, WLAN_PASSWORD)
		while not wlan.isconnected():
			state = 1 - state
			led.value(state)
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
		soil_moisture = round(100 * (1023 - pot_value) / 1023, 2)
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
	led.value(0)
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
mqtt.disconnect()
sys.exit()
