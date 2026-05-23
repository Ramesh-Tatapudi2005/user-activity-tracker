import os
import json
import time
import pika
import logging
import signal
import sys
from datetime import datetime
from src.database import SessionLocal, init_db
from src.models import UserActivity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventConsumer:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue_name = "user_activity_events"
        self.is_running = False

    def connect(self):
        host = os.getenv("RABBITMQ_HOST", "localhost")
        port = int(os.getenv("RABBITMQ_PORT", 5672))
        user = os.getenv("RABBITMQ_USER", "guest")
        password = os.getenv("RABBITMQ_PASSWORD", "guest")

        credentials = pika.PlainCredentials(user, password)
        parameters = pika.ConnectionParameters(host=host, port=port, credentials=credentials)
        
        retries = 5
        while retries > 0:
            try:
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue=self.queue_name, durable=True)
                self.channel.basic_qos(prefetch_count=1)
                logger.info("Successfully connected to RabbitMQ.")
                return
            except pika.exceptions.AMQPConnectionError:
                logger.warning("RabbitMQ connection failed. Retrying...")
                retries -= 1
                time.sleep(5)
        raise ConnectionError("Failed to connect to RabbitMQ after multiple attempts.")

    def process_message(self, ch, method, properties, body):
        session = SessionLocal()
        try:
            event_data = json.loads(body.decode())
            activity_record = UserActivity(
                user_id=event_data['user_id'],
                event_type=event_data['event_type'],
                timestamp=datetime.fromisoformat(event_data['timestamp'].replace('Z', '+00:00')),
                metadata_payload=event_data.get('metadata', {})
            )
            
            session.add(activity_record)
            session.commit()
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Successfully processed and stored event for user_id: {event_data['user_id']}")

        except json.JSONDecodeError as e:
            logger.error(f"Malformed JSON message received. Discarding. Error: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to process message due to internal error. Discarding. Error: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        finally:
            session.close()

    def start_consuming(self):
        self.connect()
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=self.process_message)
        logger.info("Started consuming messages. To exit press CTRL+C")
        self.is_running = True
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.stop()

    def stop(self, signum=None, frame=None):
        logger.info("Graceful shutdown initiated. Closing connections.")
        if self.connection and self.connection.is_open:
            self.connection.close()
        sys.exit(0)

if __name__ == "__main__":
    init_db()
    consumer = EventConsumer()
    signal.signal(signal.SIGTERM, consumer.stop)
    signal.signal(signal.SIGINT, consumer.stop)
    consumer.start_consuming()