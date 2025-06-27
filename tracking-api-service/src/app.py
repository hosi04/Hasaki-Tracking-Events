from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import time
import requests
from kafka import KafkaConsumer
import json

app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading')

CUBE_API_URL = 'http://localhost:4000/cubejs-api/v1/load'
CUBE_API_TOKEN = 'secret123'

headers = {
    'Authorization': CUBE_API_TOKEN,
    'Content-Type': 'application/json'
}

def fetch_cube(query):
    print("Đang gửi query:", query)
    res = requests.post(CUBE_API_URL, json={"query": query}, headers=headers)  # fix tại đây
    res.raise_for_status()
    return res.json().get("data", [])

# Update here
def decode(msg_value):
    message_bytes = io.BytesIO(msg_value)
    decoder = BinaryDecoder(message_bytes)
    event_dict = reader.read(decoder)
    return event_dict

def listen_dashboard_update_signal():
    try:
        consumer = KafkaConsumer('dashboard_update_signal',
                            group_id='my-group',
                            bootstrap_servers=['localhost:9092'])
        running = True
        while running:
            msg_pack = consumer.poll(timeout_ms=500)
            for tp, messages in msg_pack.items():
                for message in messages:
                    print ("%s:%d:%d: key=%s value=%s" % (tp.topic, tp.partition, message.offset,
                        message.key,
                        message.value.decode('utf-8')))
                    poll_cube() #Refresh Dashboard
    except Exception as e:
        print("Error Kafka Consumer...........")

def poll_cube():
    try:
        # Query 1: Tổng doanh thu
        revenue_data = fetch_cube({
            "measures": ["CheckoutItems.totalRevenue"]
        })
        total_revenue = revenue_data[0]["CheckoutItems.totalRevenue"] if revenue_data else 0

        # Query 2: Top sản phẩm
        product_data = fetch_cube({
            "measures": ["CheckoutItems.totalQuantity"],
            "dimensions": ["CheckoutItems.product_name"],
            "order": { "CheckoutItems.totalQuantity": "desc" },
            "limit": 10
        })
        products = [
            (row["CheckoutItems.product_name"], row["CheckoutItems.totalQuantity"])
            for row in product_data
        ]

        # Query 3: Doanh thu theo user
        user_data = fetch_cube({
            "measures": ["CheckoutItems.totalRevenue"],
            "dimensions": ["CheckoutItems.user_id"],
            "order": { "CheckoutItems.totalRevenue": "desc" },
            "limit": 10
        })
        users = [
            (row["CheckoutItems.user_id"], row["CheckoutItems.totalRevenue"])
            for row in user_data
        ]

        # Query 4: Doanh thu theo ngày
        daily_data = fetch_cube({
            "measures": ["CheckoutItems.totalRevenue"],
            "dimensions": ["CheckoutItems.timestamp"],
            "timeDimensions": [{
                "dimension": "CheckoutItems.timestamp",
                "granularity": "day"
            }],
            "order": { "CheckoutItems.timestamp": "asc" }
        })
        daily = [
            (row["CheckoutItems.timestamp"], row["CheckoutItems.totalRevenue"])
            for row in daily_data
        ]

        # Emit về client
        socketio.emit('update_data', {
            'revenue': total_revenue,
            'data': products,
            'user_revenue': users,
            'daily_revenue': daily
        })

    except Exception as e:
        print("Lỗi khi gọi Cube API:", e)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # # Poll Data From CubeDev
    # threading.Thread(target=poll_cube, daemon=True).start()
    
    # Listen Topic Here
    threading.Thread(target=listen_dashboard_update_signal, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
