import time
import json
import esp32
import sys
import sds011
import machine
from machine import UART
from network import WLAN
import network
from umqtt.robust import MQTTClient

### Settings
WLAN_ESSID = "wlan_ap"
WLAN_PASSWORD = "wlan_ap_password"
IOT_ENDPOINT = "xxxxxxxx.iot.eu-central-1.amazonaws.com"
THING = "ESP32-WROOM-32D-IOT"
TOPIC = "things/measurements"
THING_SHADOW = "$aws/things/" + THING + "/shadow/update"
KEY_PATH = "/32-01.key.der"
CERT_PATH = "/32-01.cert.der"
CACERT_PATH = "/ca_root.cert"
PVT_KEY = None
CERT_KEY = None
CA_CERT = None

### Initial setup
wlan = network.WLAN(network.STA_IF)
uart = UART(2, baudrate=9600)
dust_sensor = sds011.SDS011(uart)

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

def sds011Meas():
	print()
	print("Waking up SDS011 sensor...")
	dust_sensor.wake()
	print("Waiting for 30 seconds...")
	time.sleep(30)
	print("Getting SDS011 status...")
	status = dust_sensor.read()
	print(status)
	r = {}
	if status == True:
		r = {
			'status': 'OK',
			'pm10': dust_sensor.pm10,
			'pm25': dust_sensor.pm25
		}
	else:
		r = {
			'status': 'NOK'
		}
	print("Putting SDS011 sensor to sleep...")
	dust_sensor.sleep()
	return r

# MQTT publish
def publishMQTT(d):
	print('PM10: ' + str(d["pm10"]))
	print('PM25: ' + str(d["pm25"]))
	message = {
		"state": {
			"reported": {
				"thing": THING,
				"pm10": d["pm10"],
				"pm25": d["pm25"]
			}
		}
	}
	print(message)
	mqtt.publish(
		topic = TOPIC,
		msg = json.dumps(message)
	)
	message['state']['reported']['connected'] = True
	mqtt.publish(
		topic = THING_SHADOW,
		msg = json.dumps(message)
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
deviceIdle(5)
mqtt.connect()

# Publish measurements
while True:
	if not wlan.isconnected():
		connectToWiFi(20)
		r = sds011Meas()
		print(r)
		if r["status"] == "OK":
			publishMQTT(r)
		print()
		print("Waiting for 30 seconds...")
		deviceIdle(30)
	else:
		r = sds011Meas()
		print(r)
		if r["status"] == "OK":
			publishMQTT(r)
		print()
		print("Waiting for 30 seconds...")
		deviceIdle(30)

sys.exit()
