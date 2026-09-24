from enum import Enum
from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException, status
from pydantic import EmailStr
from sqlmodel import Field, Session, SQLModel, create_engine, select, func

# =====================================================================
# 1. DATABASE CONFIGURATION
# =====================================================================
sqlite_file_name = "events_management.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# =====================================================================
# 2. ENUMS & MODELS WITH VALIDATION
# =====================================================================
class EventStatus(str, Enum):
    OPEN = "Open"
    CLOSED = "Closed"


# --- Event Models ---
class EventBase(SQLModel):
    title: str = Field(..., min_length=1, description="Event name")
    venue: str = Field(..., min_length=1, description="Event location")
    # gt=0 ensures capacity must be greater than 0
    capacity: int = Field(..., gt=0, description="Maximum number of participants")
    organizer: str = Field(..., min_length=1, description="Organizer name")
    status: EventStatus = Field(default=EventStatus.OPEN, description="Must be Open or Closed")


class Event(EventBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class EventUpdate(SQLModel):
    title: Optional[str] = Field(default=None, min_length=1)
    venue: Optional[str] = Field(default=None, min_length=1)
    capacity: Optional[int] = Field(default=None, gt=0)
    organizer: Optional[str] = Field(default=None, min_length=1)
    status: Optional[EventStatus] = None


# --- Reservation Models ---
class ReservationBase(SQLModel):
    student_name: str = Field(..., min_length=1, description="Name of participant")
    roll_number: str = Field(..., min_length=1, description="Participant roll number")
    # EmailStr automatically handles robust email validation
    email: EmailStr = Field(..., description="Participant email")


class Reservation(ReservationBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(..., foreign_key="event.id", description="ID of the event")


# =====================================================================
# 3. FASTAPI APP INITIALIZATION
# =====================================================================
app = FastAPI(
    title="College Event Management & Reservation API",
    description="A system to manage campus events, hackathons, and student registrations.",
    version="1.0.0"
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


# =====================================================================
# 4. REQUIRED EVENT APIs (Endpoints 1 to 5)
# =====================================================================

# 1. POST /events — Create a new event
@app.post("/events", response_model=Event, status_code=status.HTTP_201_CREATED)
def create_event(event: EventBase):
    with Session(engine) as session:
        db_event = Event.model_validate(event)
        session.add(db_event)
        session.commit()
        session.refresh(db_event)
        return db_event


# 2. GET /events — Return all events
@app.get("/events", response_model=List[Event])
def read_events():
    with Session(engine) as session:
        events = session.exec(select(Event)).all()
        return events


# 3. GET /events/{event_id} — Return a specific event
@app.get("/events/{event_id}", response_model=Event)
def read_event(event_id: int):
    with Session(engine) as session:
        db_event = session.get(Event, event_id)
        if not db_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID {event_id} does not exist."
            )
        return db_event


# 4. PUT /events/{event_id} — Update event information
@app.put("/events/{event_id}", response_model=Event)
def update_event(event_id: int, event_update: EventUpdate):
    with Session(engine) as session:
        db_event = session.get(Event, event_id)
        if not db_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID {event_id} does not exist."
            )
        
        update_data = event_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_event, key, value)
            
        session.add(db_event)
        session.commit()
        session.refresh(db_event)
        return db_event


# 5. DELETE /events/{event_id} — Delete an event
@app.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int):
    with Session(engine) as session:
        db_event = session.get(Event, event_id)
        if not db_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID {event_id} does not exist."
            )
        session.delete(db_event)
        session.commit()
        return None


# =====================================================================
# 5. REQUIRED RESERVATION APIs (Endpoints 6 to 9)
# =====================================================================

# 6. POST /events/{event_id}/reserve — Create a reservation for an event
@app.post("/events/{event_id}/reserve", response_model=Reservation, status_code=status.HTTP_201_CREATED)
def create_reservation(event_id: int, reservation: ReservationBase):
    with Session(engine) as session:
        # Business Logic Rule 1: Verify that the event exists
        db_event = session.get(Event, event_id)
        if not db_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID {event_id} does not exist."
            )
        
        # Business Logic Rule 2: Verify that the event is Open
        if db_event.status == EventStatus.CLOSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reserve a seat. This event is marked as Closed."
            )
            
        # Business Logic Rule 3: Check the number of existing reservations
        booked_seats = session.exec(
            select(func.count(Reservation.id)).where(Reservation.event_id == event_id)
        ).one()
        
        # Business Logic Rule 4: Do not allow reservations if the event is already full
        if booked_seats >= db_event.capacity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration failed. The event has reached its maximum capacity of {db_event.capacity} seats."
            )
            
        # If all checks pass, save the reservation
        db_reservation = Reservation.model_validate(reservation, update={"event_id": event_id})
        session.add(db_reservation)
        session.commit()
        session.refresh(db_reservation)
        return db_reservation


# 7. GET /events/{event_id}/reservations — Return all reservations for a particular event
@app.get("/events/{event_id}/reservations", response_model=List[Reservation])
def read_event_reservations(event_id: int):
    with Session(engine) as session:
        # Check if event exists first
        db_event = session.get(Event, event_id)
        if not db_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID {event_id} does not exist."
            )
        reservations = session.exec(select(Reservation).where(Reservation.event_id == event_id)).all()
        return reservations


# 8. DELETE /reservations/{reservation_id} — Cancel a reservation
@app.delete("/reservations/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_reservation(reservation_id: int):
    with Session(engine) as session:
        db_reservation = session.get(Reservation, reservation_id)
        if not db_reservation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reservation with ID {reservation_id} does not exist."
            )
        session.delete(db_reservation)
        session.commit()
        return None


# 9. GET /events/{event_id}/availability — Return capacity details
@app.get("/events/{event_id}/availability", response_model=Dict[str, int])
def read_event_availability(event_id: int):
    with Session(engine) as session:
        db_event = session.get(Event, event_id)
        if not db_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID {event_id} does not exist."
            )
            
        booked_seats = session.exec(
            select(func.count(Reservation.id)).where(Reservation.event_id == event_id)
        ).one()
        
        remaining_seats = max(0, db_event.capacity - booked_seats)
        
        return {
            "capacity": db_event.capacity,
            "booked": booked_seats,
            "remaining": remaining_seats
        }
