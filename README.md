# Simple Pins API

## Overview
Simple Pins API is a high-performance, asynchronous RESTful web service. It allows authenticated users to securely register, manage, and share pins (containing titles, bodies, and image links). 

---

## Prerequisites

Before you begin, ensure you have the following installed on your system:
* Python 3.10+
* MySQL Server (Running locally or via Docker)
* uv (Astral's fast Python package installer and resolver)


## Local Setup

1. Clone the repository:
```sh
   git clone <repository_url>
   cd SimplePinsAPI
```

2. Install dependencies and set up the virtual environment using uv:
```sh
   uv sync
```

3. Activate the virtual environment:
```sh
   source .venv/bin/activate
```

   
## Database Configuration

1. Log into your local MySQL/MariaDB instance and create the database:
```sh
   mysql -h 127.0.0.1 -u root simple_pins_api < migrations/schema.sql
```

2. Ensure the required tables are created. (Note: Schema documentation is provided in the internal [API Design Document](docs/API_Design_Documentation.md). Tables required are User, Pin, and RefreshToken utilizing BINARY(16) for UUIDs).

3. Set your database credentials in your environment variables or the `app/core/config.py` file to match your local MySQL/MariaDB setup.


## Running the Application

Start the FastAPI application using Uvicorn:
```sh
uv run uvicorn app.main:app --reload
```

The server will start on `http://127.0.0.1:8000`. 
Note: On startup, the `DatabaseManager` will attempt to connect to MySQL/MariaDB. If the database is unavailable, Tenacity will automatically retry with exponential backoff before failing.

---

## API Documentation

API documentation is available [here](docs/API_Design_Documentation.md)

FastAPI automatically generates interactive API documentation. Once the server is running, you can access:
* Swagger UI: `http://127.0.0.1:8000/docs`
* ReDoc: `http://127.0.0.1:8000/redoc`

---

## Project Structure

* `app/main.py`: Application entry point and lifespan event definitions.
* `app/api/v1/`: API routers and endpoint definitions.
* `app/core/`: Global configuration, JWT generation, and password hashing logic.
* `app/db/`: Asynchronous database connection pooling and Semaphore controls.
* `app/schemas/`: Pydantic models for request validation and response serialization.
