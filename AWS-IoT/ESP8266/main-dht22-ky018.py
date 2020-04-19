import time
import sys
import json
import dht
import machine
from machine import Pin
from machine import ADC
from network import WLAN
import network
from umqtt.simple import MQTTClient

led = Pin(2, Pin.OUT, value=1)

### Settings
WLAN_ESSID = "WLAN_AP"
WLAN_PASSWORD = "AP_PASSWORD"
IOT_ENDPOINT = "xxxxxxxxxxxxxx-ats.iot.eu-central-1.amazonaws.com"
THING = "ESP8266-NODEMCU-V3-IOT (YOUR THING ID)"
TOPIC = "things/measurements"
THING_SHADOW = "$aws/things/" + THING + "/shadow/update"
KEY_PATH = "/8266-01.key.der"
CERT_PATH = "/8266-01.cert.der"
CACERT_PATH = "/ca_root.cert"
PVT_KEY = None
CERT_KEY = None
CA_CERT = None

### Initial setup
# Set leds and pins
wlan = network.WLAN(network.STA_IF)
adc = ADC(0)
d = dht.DHT22(machine.Pin(4))

# Load certificate and key
with open(KEY_PATH, 'rb') as f:
	PVT_KEY = f.read()
with open(CERT_PATH, 'rb') as f:
	CERT_KEY = f.read()

### Functions
# Device idle
def deviceIdle():
	time.sleep(10)
	led.value(1)
	time.sleep(45)

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

# MQTT publish
def publishMQTT():
	led.value(0)
	ky018_level = adc.read()
	d.measure()
	print('KY-018: ' + str(ky018_level))
	print('Temperature: ' + str(d.temperature()))
	print('Humidity: ' + str(d.humidity()))
	message = {
		"state": {
			"reported": {
				"thing": THING,
				"light": ky018_level,
				"temperature": d.temperature(),
				"humidity": d.humidity()
			}
		}
	}
	mqtt.publish(
		topic = 'things/measurements',
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

# Yellow LED=on
led.value(0)
mqtt.connect()
led.value(1)
time.sleep(10)

# Publish measurements
while True:
	if not wlan.isconnected():
		connectToWiFi(20)
		try:
			publishMQTT()
		except:
			machine.reset()
		deviceIdle()
	else:
		try:
			publishMQTT()
		except:
			machine.reset()
		deviceIdle()

# Disconnect
mqtt.disconnect()
led.value(1)
sys.exit()


