import paho.mqtt.client as mqtt
import json
import os
import django
import sys

# 1. Configuración de Django
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'IOTMonitoringServer.settings')
django.setup()

from django.conf import settings
from receiver.models import Data, Station, Measurement

# 2. Configuración MQTT
MQTT_HOST = settings.MQTT_HOST
MQTT_PORT = settings.MQTT_PORT

# Tópicos sincronizados con tu Arduino
TOPIC_SUB = "luminosidad/bogota/yuely" 
TOPIC_PUB = "Colombia/Bogota/Centro/Yuely/in"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Conectado exitosamente al Broker: {MQTT_HOST}")
        client.subscribe(TOPIC_SUB)
        print(f"📡 Suscrito al tópico: {TOPIC_SUB}")
    else:
        print(f"❌ Error de conexión. Código: {rc}")

# Agrega esta lista justo ARRIBA de la función on_message (fuera de ella)
lecturas_recientes = []

def on_message(client, userdata, msg):
    global lecturas_recientes
    try:
        payload = json.loads(msg.payload.decode())
        valor_luz = float(payload['value'])
        
        # 1. Intentar guardar en AWS (Capa de Persistencia)
        try:
            measure, _ = Measurement.objects.get_or_create(name="luminosidad", defaults={'unit': 'Lux'})
            Data.objects.create(measurement=measure, avg_value=valor_luz)
            print(f"📥 Persistencia: {valor_luz} Lux guardado en AWS")
        except Exception as db_err:
            print(f"⚠️ Nota: Error guardando en DB, pero seguiremos con la lógica: {db_err}")

        # 2. Lógica de Promedio (Capa de Lógica)
        # Usamos una lista local para asegurar que el video salga fluido
        lecturas_recientes.append(valor_luz)
        if len(lecturas_recientes) > 5:
            lecturas_recientes.pop(0) # Mantener solo las últimas 5
        
        promedio = sum(lecturas_recientes) / len(lecturas_recientes)
        print(f"📊 PROMEDIO ACTUAL: {promedio:.2f} Lux")

        # 3. Decisión de Actuación (Capa de Red / Actuación)
        if promedio < 400:
            client.publish(TOPIC_PUB, json.dumps({"led": "on"}))
            print("💡 >>> EVENTO: LUZ BAJA - ENVIANDO LED ON")
        else:
            client.publish(TOPIC_PUB, json.dumps({"led": "off"}))
            print("🌑 >>> EVENTO: LUZ OK - ENVIANDO LED OFF")

    except Exception as e:
        print(f"❌ Error crítico: {e}")

# 3. Inicialización del Cliente con versión de API 1 (para evitar el cierre súbito)
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
client.on_connect = on_connect
client.on_message = on_message

try:
    print(f"⏳ Intentando conectar a {MQTT_HOST}...")
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    # Mantener el script corriendo
    client.loop_forever()
except Exception as e:
    print(f"❌ No se pudo iniciar el script: {e}")