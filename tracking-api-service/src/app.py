from flask import Flask, render_template
from flask_socketio import SocketIO
import clickhouse_connect
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading')  # Thêm async_mode để tránh xung đột

# Kết nối ClickHouse
client = clickhouse_connect.get_client(host='localhost', port=8123)

def poll_clickhouse():
    while True:
        try:
            # Truy vấn: thống kê số lần checkout theo sản phẩm
            result = client.query("""
                SELECT product_name, count(*) AS total
                FROM tracking_problem.checkout_items
                GROUP BY product_name
                ORDER BY total DESC
            """).result_rows

            # Gửi dữ liệu đến frontend
            socketio.emit('update_data', {'data': result})
        except Exception as e:
            print("Lỗi khi truy vấn ClickHouse hoặc gửi dữ liệu:", e)

        time.sleep(5)  # Mỗi 5 giây query lại

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # Chạy polling trong thread riêng (daemon để dừng khi app tắt)
    threading.Thread(target=poll_clickhouse, daemon=True).start()

    # Bắt đầu Flask + SocketIO
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
