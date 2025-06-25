from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json

from kafka import KafkaConsumer,KafkaProducer

app = FastAPI()

# Cấu hình CORS để cho phép website trên localhost:5500 gửi yêu cầu
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500"],  # Origin của website
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

producer = KafkaProducer(bootstrap_servers='localhost:9092', value_serializer=lambda v: json.dumps(v).encode('utf-8'))

# Endpoint nhận POST /track
@app.post("/track")
async def track_event(request: Request):
    event_data = await request.json()
    print("Received event:", json.dumps(event_data, indent=2, ensure_ascii=False))

    # Send data to Kafka
    try:
        producer.send("test-topic", event_data)
        producer.flush() # Send data
        return {"message": "Event sent to Kafka topic 'test-topic'"}
    except Exception as e:
        print("Kafka error:", str(e))
        return {"error": "Failed to send event to Kafka"}

    