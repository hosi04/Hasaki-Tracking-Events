from flask import Flask, render_template
from flask_socketio import SocketIO
import clickhouse_connect
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading')

# Kết nối ClickHouse
client = clickhouse_connect.get_client(
    host='localhost',
    port=8123,
    user='default',
    password='',
    database='tracking_problem'
)

def poll_clickhouse():
    while True:
        try:
            # 1. Top sản phẩm được checkout
            product_result = client.query("""
                SELECT
                    product_name,
                    sum(toUInt32(quantity)) AS total
                FROM tracking_problem.checkout_items
                GROUP BY product_name
                ORDER BY total DESC
            """).result_rows

            # 2. Tổng doanh thu toàn hệ thống
            revenue_result = client.query("""
                SELECT SUM(toUInt32(product_price) * toUInt32(quantity)) AS total_revenue
                FROM tracking_problem.checkout_items
            """).result_rows
            total_revenue = revenue_result[0][0] if revenue_result else 0

            # 3. Tổng doanh thu theo khách hàng
            user_revenue_result = client.query("""
                SELECT
                    user_id,
                    SUM(toUInt32(product_price) * toUInt32(quantity)) AS revenue
                FROM tracking_problem.checkout_items
                GROUP BY user_id
                ORDER BY revenue DESC
            """).result_rows

            # Emit về frontend
            socketio.emit('update_data', {
                'data': product_result,
                'revenue': total_revenue,
                'user_revenue': user_revenue_result
            })
            # 4. Doanh thu theo ngày
            daily_revenue_result = client.query("""
                SELECT
                    toDate(timestamp) AS day,
                    SUM(toUInt32(product_price) * toUInt32(quantity)) AS revenue
                FROM tracking_problem.checkout_items
                GROUP BY day
                ORDER BY day
            """).result_rows

            # Chuyển date -> string để JSON hóa
            daily_revenue_serializable = [(str(day), revenue) for day, revenue in daily_revenue_result]

            # Emit toàn bộ
            socketio.emit('update_data', {
                'data': product_result,
                'revenue': total_revenue,
                'user_revenue': user_revenue_result,
                'daily_revenue': daily_revenue_serializable
            })

        except Exception as e:
            print("Lỗi khi truy vấn ClickHouse hoặc gửi dữ liệu:", e)

        time.sleep(3)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    threading.Thread(target=poll_clickhouse, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
