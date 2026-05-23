# Event-Driven User Activity Tracking System

## Project Overview
This project is a highly scalable, decoupled backend system designed to track user activities (e.g., logins, page views, checkouts) in real-time. Moving away from traditional, tightly-coupled synchronous request-response models, this system utilizes an **event-driven architecture**. 

By offloading heavy database write operations to a background consumer service via a message broker, the primary ingestion API remains highly available, responsive, and resilient to downstream latency or database outages.

## Architectural Decisions
* **Producer API (FastAPI):** Selected for its native asynchronous capabilities and lightning-fast execution. Pydantic is utilized for strict, automatic input validation, ensuring corrupted data never enters the processing pipeline.
* **Message Broker (RabbitMQ):** Chosen for its robust delivery guarantees and strict adherence to the AMQP protocol. It acts as a resilient buffer, utilizing explicit message acknowledgments to ensure zero data loss during consumer downtime.
* **Consumer Service (Python/SQLAlchemy):** Built as a completely standalone, independent worker process. It relies on a robust connection retry mechanism and SQLAlchemy for secure, optimized insertion of event data into the persistent storage layer.
* **Data Persistence (MySQL 8.0):** Utilized as the primary datastore, automatically initialized with a normalized schema tailored for high-volume activity logging.
* **Containerization (Docker Compose):** The entire system is orchestrated via Docker Compose, complete with localized volume mounting for testing and strict health check dependencies to control startup sequences.

## Setup & Deployment Instructions

### Prerequisites
* Docker and Docker Compose installed on your local machine.
* Git for cloning the repository.

### Quick Start
1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Ramesh-Tatapudi2005/user-activity-tracker.git]
   cd user-activity-tracker
   ```  

### Configure Environment Variables
Copy the example environment file and adjust if necessary (the defaults work out of the box for local Docker execution).

```bash
cp .env.example .env
```

### Launch the System
Build the images and start all services in detached mode.

```bash
docker-compose up --build -d
```

### Verify Health
Ensure all four containers (RabbitMQ, MySQL, Producer, Consumer) are marked as healthy:

```bash
docker-compose ps
```

## API Endpoint Documentation
Once the system is running, the interactive Swagger API documentation is available at: `http://localhost:8000/docs`.

### 1. Track User Activity
**`POST /api/v1/events/track`**

Ingests a user activity event and publishes it to the message queue for background processing.

**Request Body Schema (`application/json`)**
```json
{
  "user_id": 123,
  "event_type": "page_view",
  "timestamp": "2023-10-27T10:00:00Z",
  "metadata": {
    "page_url": "/products/item-xyz",
    "session_id": "abc123"
  }
}
```

**Responses:**
* `202 Accepted`: Event successfully validated and published to the queue.
* `400 Bad Request`: Invalid payload structure, missing required fields, or incorrect data types.
* `500 Internal Server Error`: Message broker connection failure.

### 2. Service Health Check
**`GET /health`**

Returns `200 OK` `{"status": "healthy"}` if the API is operational and the message broker is connected.

## Automated Testing
The system includes isolated test suites for both the Producer and Consumer services. Tests are executed directly inside the running Docker containers using volume mounts, ensuring environment parity.

**Run Producer Tests:**
```bash
docker-compose exec producer-service python -m pytest tests/test_producer.py
```

**Run Consumer Tests:**
```bash
docker-compose exec consumer-service python -m pytest tests/test_consumer.py
```

## Challenges Faced & Solutions Implemented

**1. Microservice Startup Race Conditions:**
* **Challenge:** During the initial `docker-compose up`, the FastAPI producer and Python consumer would crash because RabbitMQ required several seconds to initialize its internal network, resulting in `ConnectionRefusedError` exceptions.
* **Solution:** Engineered an asynchronous, exponential backoff and retry mechanism in the connection lifecycle events of both Python services. The applications now gracefully wait and re-attempt connections until the AMQP port becomes fully available.

**2. Strict Protocol Compliance:**
* **Challenge:** FastAPI natively returns a `422 Unprocessable Entity` for schema validation failures, but strict system requirements dictated a `400 Bad Request` for malformed events.
* **Solution:** Implemented a custom global exception handler in FastAPI to intercept `RequestValidationError` events and correctly map them to the standard `400` HTTP status code while preserving the detailed schema error messages.

**3. Database Authentication Compatibility:**
* **Challenge:** Upgrading to MySQL 8.0 introduced the `caching_sha2_password` authentication plugin, causing standard `PyMySQL` connections in the consumer to fail.
* **Solution:** Integrated the `cryptography` Python package into the consumer's environment, allowing SQLAlchemy to successfully negotiate the modern cryptographic handshake without compromising security by downgrading the database settings.
