import json
import os
from datetime import datetime, timedelta
import time
import uuid
from confluent_kafka import SerializingProducer
import random

KAMPALA_COORDINATES = {
    "latitude": 0.3152,
    "longitude": 32.5816
}
MUKONO_COORDINATES = {
    "latitude": 0.3689,
    "longitude": 32.7135
}

# movement calculation
LATITUDE_INCREMENT = (MUKONO_COORDINATES['latitude'] - KAMPALA_COORDINATES['latitude']) / 100
LONGITUDE_INCREMENT = (MUKONO_COORDINATES['longitude'] - KAMPALA_COORDINATES['longitude']) / 100

# environment variables for configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
VEHICLE_TOPIC = os.getenv('VEHICLE_TOPIC', 'vehicle_data')
GPS_TOPIC = os.getenv('GPS_TOPIC', 'gps_data')
TRAFFIC_TOPIC = os.getenv('TRAFFIC_TOPIC', 'traffic_data')
WEATHER_TOPIC = os.getenv('WEATHER_TOPIC', 'weather_data')
EMERGENCY_TOPIC = os.getenv('EMERGENCY_TOPIC', 'emergency_data')

start_time = datetime.now()
start_location = KAMPALA_COORDINATES.copy()

def generate_emergency_incident_data(device_id, timestamp, location):
    return {
        'id': uuid.uuid4(),  
        'deviceId': device_id,
        'timestamp': timestamp,
        'location': location,
        'incidentId': uuid.uuid4(),  
        'type': random.choice(['Accident', 'Fire', 'Medical', 'Police', 'None']),
        'status': random.choice(['Active', 'Resolved']),
        'description': 'Description of the incident'
    }

def generate_weather_data(device_id, timestamp, location):
    return {
        'id': device_id,
        'timestamp': timestamp,
        'location': location,
        'temperature': random.uniform(-5, 25),
        'weatherCondition': random.choice(['Sunny', 'Cloudy', 'Rainy', 'Snowy']),
        'precipitation': random.uniform(0, 25),
        'windSpeed': random.uniform(0, 100),
        'humidity': random.randint(0, 100),
        'airQualityIndex': random.uniform(0, 500)
    }

def generate_traffic_camera_data(device_id, timestamp, location, camera_id):
    return {
        'id': uuid.uuid4(),  
        'deviceId': device_id,
        'location': location,
        'cameraId': camera_id,
        'timestamp': timestamp,
        'snapshot': 'Base64EncodedString',
    }

def generate_gps_data(device_id, timestamp, vehicle_type='private'):
    return {
        'id': uuid.uuid4(),  
        'device_id': device_id,
        'timestamp': timestamp,
        'speed': random.uniform(0, 40), # km/h
        'direction': 'North-East',
        'vehicleType': vehicle_type
    }

def get_next_time():
    global start_time
    start_time += timedelta(seconds=random.randint(30, 60))
    return start_time

def simulate_vehicle_movement():
    global start_location

    # move towards Mukono
    start_location['latitude'] += LATITUDE_INCREMENT
    start_location['longitude'] += LONGITUDE_INCREMENT

    # Adding randomness to simulate the actual travel
    start_location['latitude'] += random.uniform(-0.0005, 0.0005)
    start_location['longitude'] += random.uniform(-0.0005, 0.0005)

    return start_location

def generate_vehicle_data(device_id):
    location = simulate_vehicle_movement()
    return {
        'id': uuid.uuid4(),  
        'deviceId': device_id,
        'timestamp': get_next_time().isoformat(),
        'location': (location['latitude'], location['longitude']),
        'speed': random.uniform(10, 40),
        'direction': 'North-East',
        'make': 'Tesla',
        'model': 'S',
        'year': 2024,
        'fuelType': 'Electric'
    }

def json_serializer(obj):
    if isinstance(obj, uuid.UUID):
        return str(obj)
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

def produce_data_to_kafka(producer, topic, data):
    producer.produce(
        topic,
        key=str(data['id']),
        value=json.dumps(data, default=json_serializer).encode('utf-8'),
        on_delivery=delivery_report
    )

    producer.flush()

def simulate_journey(producer, device_id):
    while True:
        vehicle_data = generate_vehicle_data(device_id)
        gps_data = generate_gps_data(device_id, vehicle_data['timestamp'])
        traffic_camera_data = generate_traffic_camera_data(device_id, vehicle_data['timestamp'], vehicle_data['location'], camera_id='Nikon-camera123')
        weather_data = generate_weather_data(device_id, vehicle_data['timestamp'], vehicle_data['location'])
        emergency_incident_data = generate_emergency_incident_data(device_id, vehicle_data['timestamp'], vehicle_data['location'])


        if (vehicle_data['location'][0] >= MUKONO_COORDINATES['latitude'] and vehicle_data['location'][1] <= MUKONO_COORDINATES['longitude']):
            print('Vehicle has reached Birmingham. Simulation ending')

            break

        produce_data_to_kafka(producer, VEHICLE_TOPIC, vehicle_data)
        produce_data_to_kafka(producer, GPS_TOPIC, gps_data)
        produce_data_to_kafka(producer, TRAFFIC_TOPIC, traffic_camera_data)
        produce_data_to_kafka(producer, WEATHER_TOPIC, weather_data)
        produce_data_to_kafka(producer, EMERGENCY_TOPIC, emergency_incident_data)

        time.sleep(2)

if __name__ == '__main__':
    producer_config = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'error_cb': lambda err: print(f"kafka err: {err}")
    }

    producer = SerializingProducer(producer_config)

    try:
        simulate_journey(producer, 'Vehicle-Kofi-123')
    except KeyboardInterrupt:
        print('Simulation ended by the user')
    except Exception as e:
        print(f"Unexpected Error occurred: {e}")
