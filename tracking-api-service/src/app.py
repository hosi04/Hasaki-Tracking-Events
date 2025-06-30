from flask import Flask, render_template, request
from flask_socketio import SocketIO
import threading
import requests
from kafka import KafkaConsumer
import json
import time
import traceback

app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

CUBE_API_URL = 'http://localhost:4000/cubejs-api/v1/load'
CUBE_API_TOKEN = 'secret123'

headers = {
    'Authorization': CUBE_API_TOKEN,
    'Content-Type': 'application/json'
}

def listen_dashboard_update_signal():
    try:
        consumer = KafkaConsumer(
            'dashboard_update_signal',
            group_id=f'my-group-{int(time.time())}',
            bootstrap_servers=['localhost:9092'],
            auto_offset_reset='latest'
        )
        while True:
            msg_pack = consumer.poll(timeout_ms=1000)
            for tp, messages in msg_pack.items():
                for message in messages:
                    print(f"Received Kafka message: {message.value.decode('utf-8')}")
                    socketio.emit('dashboard_refresh', namespace='/')
    except Exception as e:
        print(f"Kafka Consumer Error: {e}\n{traceback.format_exc()}")

@app.route('/')
def index():
    """Render trang dashboard."""
    return render_template('index.html')

if __name__ == '__main__':
    threading.Thread(target=listen_dashboard_update_signal, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)