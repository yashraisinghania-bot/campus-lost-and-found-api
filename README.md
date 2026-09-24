# College Management REST APIs (Lost & Found & Event Registrations)

A unified FastAPI-based backend application featuring two micro-modules: a digital campus **Lost & Found System** and a technical **Event Booking & Reservation Management System** built with strict schema validation and business logic rules.

---

## 🛠️ Technologies Used
* **Backend Framework:** FastAPI (Asynchronous Python Web Framework)
* **ORM / Model Layer:** SQLModel (Combines Pydantic data validation with SQLAlchemy ORM mappings)
* **Database Engine:** SQLite (File-based relational database)
* **Server Gateway:** Uvicorn (ASGI server implementation)
* **Validation Dependencies:** Pydantic Core & EmailStr

---

## 📂 Project Repository Structure
```text
├── main.py                 # Task 1: Lost & Found API implementation
├── main_2.py               # Task 2: Event Registration & Capacity Logic API
├── lost_and_found.db       # SQLite Database generated for Task 1
├── events_management.db    # SQLite Database generated for Task 2
├── requirements.txt        # Shared python environmental dependencies
├── README.md               # Complete setup documentation and guidelines
└── screenshots/            # Proof of work images verifying API endpoints
```

---

## 🚀 Installation & Local Setup Steps

Follow these sequential steps to run the microservices locally on your system:

### 1. Clone or Download the Project
Ensure you have cloned or downloaded this repository to your local computer path.

### 2. Install Project Dependencies
Open your local Terminal or Command Prompt (`CMD`) inside the project root directory and install the required modules:
```bash
pip install fastapi uvicorn sqlmodel pydantic[email]
```

---

## 🏃 Commands to Run the Applications

Since both tasks run as independent modules using separate database storage layers, use their respective execution routes:

### To run Task 1 (Lost & Found System):
```bash
python -m uvicorn main:app --reload
```
* **Interactive Swagger UI URL:** [http://127.0.0](http://127.0.0)

### To run Task 2 (Event Management & Reservations):
```bash
python -m uvicorn main_2:app --reload
```
* **Interactive Swagger UI URL:** [http://127.0.0](http://127.0.0)

---

## 📑 Brief Description of Available Endpoints

### 🎒 Task 1 — Lost & Found System Route Layout
* `POST /items`: Registers a newly reported lost/found campus item. Validates that the input title is non-empty and restricts status strictly to `Lost`, `Found`, or `Returned`.
* `GET /items`: Pulls down the complete array list of all items currently cataloged inside the database.
* `GET /items/{item_id}`: Retrieves specific item records. Explicitly throws a structured `404 Not Found` response if the record ID is missing.
* `PUT /items/{item_id}`: Performs safe, delta state modifications on details or alters status tags tracking item progression.
* `DELETE /items/{item_id}`: Disposes of an invalid or outdated item record, clearing it out from database tables.
* `GET /items/status/{status}`: Provides rapid search matching to filter objects by active lifecycle states (`Lost`, `Found`, or `Returned`).
* `GET /items/category/{category}`: Pulls data matched strictly against a category string (e.g., `Electronics`, `Accessories`).

### 🎟️ Task 2 — Campus Event & Reservation Route Layout
* `POST /events`: Declares a new event entry with custom `capacity` validation requirements ensuring bounds are strictly greater than zero (`gt=0`).
* `GET /events`: Lists all scheduled operations, seminars, hackathons, and technical event entries.
* `GET /events/{event_id}`: Inspects detailed structural characteristics of a targeted event ID sequence.
* `PUT /events/{event_id}`: Updates logistics, layout constraints, schedules, or updates lifecycle operational states (`Open` vs `Closed`).
* `DELETE /events/{event_id}`: Completely drops an event record from the schema.
* `POST /events/{event_id}/reserve`: Books a seat. Employs strong logic checks checking that the event exists, is explicitly marked `Open`, and blocks execution with an explicit `400 Bad Request` if current counts hit the maximum capacity limit.
* `GET /events/{event_id}/reservations`: Fetches a complete roster of registered student names, roll numbers, and validated emails for a designated event.
* `GET /events/{event_id}/availability`: Returns a real-time availability breakdown structured as a JSON matrix displaying `capacity`, `booked` counts, and dynamically solved `remaining` seats.
* `DELETE /reservations/{reservation_id}`: Cancels a reservation by its unique reservation ID, safely freeing up a capacity seat spot.

---

## 📸 Proof of Work (Screenshots)
All functional behavior verification captures demonstrating successful responses, query filters, capacity boundary checks, and `422 Unprocessable Entity` entry level data validation handling are cleanly stored inside the `/screenshots` directory of this repository.
