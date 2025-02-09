from machine import Pin
import dht
import time
import network
from umqtt.simple import MQTTClient

# Configuración del sensor DHT11
DHT_PIN = 16  # GPIO donde conectaste el DHT11
sensor = dht.DHT11(Pin(DHT_PIN))

# Configuración del LED
led = Pin(2, Pin.OUT)
led.value(0)

# Configuración WiFi (tu red doméstica)
WIFI_SSID = "iPhone de Noe"
WIFI_PASSWORD = "123412345"

# Configuración MQTT
MQTT_CLIENT_ID = "esp32_dht11"
MQTT_BROKER = "172.20.10.4"   
MQTT_PORT = 1883
MQTT_TOPIC_PUB = "ncm/sensor"
MQTT_TOPIC_SUB = "led/control"

# Variables para almacenar los últimos valores enviados
ultima_temperatura = None
ultima_humedad = None

# Función para conectar a WiFi
def conectar_wifi():
    print("Conectando a WiFi...", end="")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
    while not sta_if.isconnected():
        print(".", end="")
        time.sleep(0.3)
    print("\nWiFi Conectada!")

# Función para suscribirse al broker MQTT
def subscribir():
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
    client.set_callback(llegada_mensaje)
    client.connect()
    client.subscribe(MQTT_TOPIC_SUB)
    print(f"Conectado a {MQTT_BROKER}, suscrito a {MQTT_TOPIC_SUB}")
    return client

# Función para recibir mensajes MQTT y controlar el LED
def llegada_mensaje(topic, msg):
    print(f"Mensaje recibido en {topic}: {msg}")
    if msg == b"true":
        led.value(1)
    elif msg == b"false":
        led.value(0)

# Conectar a WiFi
conectar_wifi()

# Conectar al broker MQTT en la Raspberry Pi
client = subscribir()

# Ciclo infinito para leer el sensor y enviar los datos a Node-RED solo si cambian
while True:
    client.check_msg()  # Revisar si hay mensajes en el topic de control
    try:
        sensor.measure()
        temperatura = sensor.temperature()  # Obtiene temperatura como entero
        humedad = sensor.humidity()  # Obtiene humedad como entero

        # Solo publicamos si cambia la temperatura o la humedad
        if temperatura != ultima_temperatura or humedad != ultima_humedad:
            datos = f"{temperatura},{humedad}"
            print(f"Publicando: Temperatura {temperatura}°C, Humedad {humedad}%")
            client.publish(MQTT_TOPIC_PUB, datos)

            # Guardamos los valores actuales para comparaciones futuras
            ultima_temperatura = temperatura
            ultima_humedad = humedad

    except OSError as e:
        print("Error al leer el sensor:", e)

    time.sleep(2)  # Leer cada 2 segundos