import paho.mqtt.client as mqtt
import json
import time
import random

# CONFIGURACIÓN SINCRONIZADA CON TU LÓGICA
MQTT_HOST = "broker.hivemq.com"  
MQTT_PORT = 1883

# DEBES usar el tópico que escucha tu script de lógica
TOPIC = "luminosidad/bogota/yuely"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(" ¡Conectado! El simulador está enviando datos de LUMINOSIDAD.")
    else:
        print(f" Error de conexión: {rc}")

client = mqtt.Client()
# El broker público no suele pedir user/pass, pero los dejamos si los necesitas
# client.username_pw_set("admin2", "admin2") 
client.on_connect = on_connect

try:
    print(f"Intentando conectar a {MQTT_HOST}...")
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()

    while True:
        # IMPORTANTE: Cambiamos 'valor' por 'value' para que el script de escucha lo entienda
        payload = {
            "variable": "luminosidad",
            "value": round(random.uniform(300.0, 500.0), 2), # Valores cerca del umbral de 400
            "latitud": 4.6097,
            "longitud": -74.0817
        }
        client.publish(TOPIC, json.dumps(payload))
        print(f" Enviado a {TOPIC}: {payload}")
        time.sleep(5) # Envía cada 5 segundos para que veas el promedio rápido
except Exception as e:
    print(f" Error: {e}")