from fastapi import FastAPI
from kafka import KafkaProducer, KafkaConsumer
import pandas as pd
import json

app = FastAPI()

producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

@app.get("/")
def root():
    return {"message": "FastAPI + Kafka is running!"}

@app.post("/send/{topic}")
def send_messages(topic: str, message:dict ):
    producer.send(topic, message )
    return {"status": "message sent", "topic": topic, "message": message}

app.get("/consumer/{topic}")
def consumer_messages(topic: str):
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers='kafka:9092',
        auto_offset_reset='earliest',
        consumer_timeout_ms=1000,
        Value_deserializer=lambda v: json.loads(v.decode('utf-8'))
    )
    messages = [msg.value for msg in consumer]
    df = pd.DataFrame(messages)
    return {"topic": topic, "df": df.to_drict(orient="record")}
