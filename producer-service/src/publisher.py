import os
import json
import asyncio
import aio_pika
import logging

logger = logging.getLogger(__name__)

class RabbitMQPublisher:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue_name = "user_activity_events"

    async def connect(self):
        host = os.getenv("RABBITMQ_HOST", "localhost")
        port = int(os.getenv("RABBITMQ_PORT", 5672))
        user = os.getenv("RABBITMQ_USER", "guest")
        password = os.getenv("RABBITMQ_PASSWORD", "guest")
        
        url = f"amqp://{user}:{password}@{host}:{port}/"
        
        retries = 5
        while retries > 0:
            try:
                self.connection = await aio_pika.connect_robust(url)
                self.channel = await self.connection.channel()
                
                queue = await self.channel.declare_queue(self.queue_name, durable=True)
                self.exchange = self.channel.default_exchange
                return # Exit the function if successful
            except Exception as e:
                logger.warning(f"RabbitMQ connection failed. Retrying... {e}")
                retries -= 1
                await asyncio.sleep(5)
                
        raise ConnectionError("Failed to connect to RabbitMQ after multiple attempts.")

    async def publish_event(self, event_data: dict):
        if not self.exchange:
            raise ConnectionError("RabbitMQ connection is not established.")
            
        message_body = json.dumps(event_data, default=str).encode()
        message = aio_pika.Message(
            body=message_body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        
        await self.exchange.publish(message, routing_key=self.queue_name)

    async def close(self):
        if self.connection:
            await self.connection.close()

publisher = RabbitMQPublisher()