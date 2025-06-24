from kafka import KafkaConsumer,KafkaProducer
import time
import io
from avro.io import DatumReader, BinaryDecoder
import avro.schema
import json
consumer = KafkaConsumer('test-topic',
                         group_id='my-group',
                         bootstrap_servers=['localhost:9092'])
def decode(msg_value):
    message_bytes = io.BytesIO(msg_value)
    decoder = BinaryDecoder(message_bytes)
    event_dict = reader.read(decoder)
    return event_dict

running = True
while running:
    # Response format is {TopicPartiton('topic1', 1): [msg1, msg2]}
    msg_pack = consumer.poll(timeout_ms=500)

    for tp, messages in msg_pack.items():
    #print (messages)
        for message in messages:
            # message value and key are raw bytes -- decode if necessary!
            # e.g., for unicode: `message.value.decode('utf-8')`   
            print ("%s:%d:%d: key=%s value=%s" % (tp.topic, tp.partition, message.offset,
                message.key,
                message.value.decode('utf-8')))
                #decode(message.value)))