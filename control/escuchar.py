import paho.mqtt.client as mqtt
import json
import os
import django
import sys

# --- 1. CONFIGURACIÓN DE ENTORNO DJANGO ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'IOTMonitoringServer.settings')
django.setup()

from receiver.models import Data, Station, Measurement

# --- 2. CONFIGURACIÓN MQTT (Solución al Timeout) ---
# Usamos un broker público para evitar bloqueos de red y cumplir con el reto ahora
MQTT_HOST = "broker.hivemq.com" 
MQTT_USER = "" 
MQTT_PASS = "" 

# Tópicos: Lectura (out) y Acción/Actuador (in)
TOPICO_LECTURA = "luminosidad/bogota/yuely"
TOPICO_ACCION = "Colombia/Bogota/Centro/Yuely/in"

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        # Buscamos tu estación creada en el Admin
        station = Station.objects.get(user__username='yuely') 

        if 'value' in payload:
            valor_luz = float(payload['value'])
            # A. Persistencia: Guardamos el dato actual
            save_to_db(station, "luminosidad", valor_luz)
            
            # B. RETO DE LÓGICA: Condición + Acción 
            ejecutar_logica_evento(client, station)

    except Exception as e:
        print(f"❌ Error procesando mensaje: {e}")

def save_to_db(station_obj, measure_name, value):
    try:
        measure_obj = Measurement.objects.get(name=measure_name)
        nueva_data = Data(
            station=station_obj,
            measurement=measure_obj,
            avg_value=value,
            values=[value],
            length=1
        )
        nueva_data.save() 
        print(f"✅ [DB] {measure_name} guardada: {value}")
    except Exception as e:
        print(f"❌ Error al guardar en DB: {e}")

def ejecutar_logica_evento(client, station_obj):
    """
    Cumple los requisitos del reto:
    1. Consulta a la base de datos[cite: 25].
    2. Evaluación de condición[cite: 23].
    3. Ejecución de acción en actuador[cite: 27].
    """
    # 1. CONSULTA A DB: Obtenemos el promedio de las últimas 5 lecturas
    ultimas_lecturas = Data.objects.filter(
        station=station_obj, 
        measurement__name='luminosidad'
    ).order_by('-id')[:5]
    
    if ultimas_lecturas.count() >= 5:
        promedio_db = sum(d.avg_value for d in ultimas_lecturas) / 5
        print(f"📊 Promedio calculado desde DB: {promedio_db}")

        # 2. CONDICIÓN: Si el promedio de luz es bajo (oscuridad)
        if promedio_db < 400: 
            # 3. ACCIÓN: Enviar comando al LED (Actuador) [cite: 27]
            comando = json.dumps({"led": "on"})
            client.publish(TOPICO_ACCION, comando)
            print("💡 EVENTO: Poca luz detectada. Enviando comando LED ON.")
        else:
            client.publish(TOPICO_ACCION, json.dumps({"led": "off"}))
            print("🌑 EVENTO: Luz suficiente. Enviando comando LED OFF.")

# --- 3. INICIO DEL CLIENTE ---
client = mqtt.Client()
client.on_message = on_message

print(f"🔗 Conectando al broker público {MQTT_HOST}...")
try:
    client.connect(MQTT_HOST, 1883, 60)
    client.subscribe(TOPICO_LECTURA)
    print(f"📡 Suscrito a: {TOPICO_LECTURA}")
    client.loop_forever()
except Exception as e:
    print(f"❌ Error de conexión: {e}")