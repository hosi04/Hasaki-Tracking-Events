from flask import Flask, render_template, request
from flask_socketio import SocketIO
import threading
import requests
from kafka import KafkaConsumer
import json
import time
import traceback

app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading')

CUBE_API_URL = 'http://localhost:4000/cubejs-api/v1/load'
CUBE_API_TOKEN = 'secret123'

headers = {
    'Authorization': CUBE_API_TOKEN,
    'Content-Type': 'application/json'
}

def force_refresh_cube():
    try:
        print("Sending Cube refresh request...")
        res = requests.post("http://localhost:4000/cubejs-api/v1/run-refresh", headers=headers)
        res.raise_for_status()
        print("Cube refresh request sent")
        time.sleep(10)  # Tăng thời gian chờ
        print("Cube refresh completed")
    except Exception as e:
        print("Cube refresh failed:", e, traceback.format_exc())

def fetch_cube(query):
    print("Sending query:", query)
    res = requests.post(CUBE_API_URL, json={"query": query}, headers=headers)
    res.raise_for_status()
    data = res.json().get("data", [])
    print("Data returned from Cube.js:", data)
    return data

# Function lang nghe tin hieu thay doi dashboard
def listen_dashboard_update_signal():
    try:
        consumer = KafkaConsumer('dashboard_update_signal',
                                 group_id='my-group',
                                 bootstrap_servers=['localhost:9092'])
        while True:
            msg_pack = consumer.poll(timeout_ms=500)
            for tp, messages in msg_pack.items():
                for message in messages:
                    print(f"Kafka message: {message.value.decode('utf-8')}")
                    force_refresh_cube()
                    socketio.emit('dashboard_refresh') # Goi Signal len Server
    except Exception as e:
        print("Kafka Consumer Error:", e)



@app.route('/query', methods=['POST'])
def dynamic_query():
    try:
        query = request.json.get("query")
        if not query:
            return {"error": "Missing query"}, 400

        force_refresh_cube()
        data = fetch_cube(query)
        return {"data": data}, 200, {'Cache-Control': 'no-cache, no-store, must-revalidate'}
    except Exception as e:
        print("Query error:", e, traceback.format_exc())
        return {"error": str(e)}, 500

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    threading.Thread(target=listen_dashboard_update_signal, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)