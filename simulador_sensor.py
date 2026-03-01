import paho.mqtt.client as mqtt
import json
import time
import random

# Configuración del Broker (obtenida de tu settings.py)
MQTT_HOST = "54.211.242.155" 
MQTT_PORT = 1883
MQTT_USER = "admin2"
MQTT_PASS = "admin2"

# Tópico: <país>/<estado>/<ciudad>/<usuario>/out
# Usaremos 'Yuely' porque es uno de tus usuarios creados
TOPIC = "Colombia/Bogota/Centro/Yuely/out"

client = mqtt.Client()
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.connect(MQTT_HOST, MQTT_PORT)

print("Simulador de sensor iniciado. Enviando datos...")

while True:
    data = {
        "variable": "temperatura",
        "valor": round(random.uniform(15.0, 25.0), 2),
        "latitud": 4.6097,
        "longitud": -74.0817
    }
    client.publish(TOPIC, json.dumps(data))
    print(f"Enviado a {TOPIC}: {data}")
    time.sleep(5)