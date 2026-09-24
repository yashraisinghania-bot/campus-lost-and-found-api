from enum import Enum
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

# =====================================================================
# 1. DATABASE CONFIGURATION
# =====================================================================
sqlite_file_name = "lost_and_found.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# connect_args={"check_same_thread": False} is required for SQLite in FastAPI
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# =====================================================================
# 2. MODELS & VALIDATION REQUIREMENTS
# =====================================================================
# Enum to restrict status values strictly to Lost, Found, or Returned
class ItemStatus(str, Enum):
    LOST = "Lost"
    FOUND = "Found"
    RETURNED = "Returned"


# Base properties shared for creating or updating items
class ItemBase(SQLModel):
    # min_length=1 ensures the title cannot be an empty string
    title: str = Field(..., min_length=1, description="Name/title of the item")
    # min_length=3 ensures the description contains meaningful text
    description: str = Field(..., min_length=3, description="Detailed description of the item")
    category: str = Field(..., description="Category like Electronics, Documents, etc.")
    location: str = Field(..., description="Location where the item was lost/found")
    reported_by: str = Field(..., description="Name of the person reporting it")
    status: ItemStatus = Field(..., description="Must be 'Lost', 'Found', or 'Returned'")


# The actual Database Table model
class Item(ItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


# Schema used for updating existing items (all fields optional to allow partial updates)
class ItemUpdate(SQLModel):
    title: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = Field(default=None, min_length=3)
    category: Optional[str] = None
    location: Optional[str] = None
    reported_by: Optional[str] = None
    status: Optional[ItemStatus] = None


# =====================================================================
# 3. FASTAPI APP INITIALIZATION
# =====================================================================
app = FastAPI(
    title="College Lost & Found API",
    description="A digital tracking system for lost, found, and returned items on campus.",
    version="1.0.0"
)


# Create the database tables on application startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()


# =====================================================================
# 4. REQUIRED API ENDPOINTS
# =====================================================================

# 1. POST /items — Create a new lost/found item
@app.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemBase):
    with Session(engine) as session:
        db_item = Item.model_validate(item)
        session.add(db_item)
        session.commit()
        session.refresh(db_item)
        return db_item


# 2. GET /items — Return all reported items
@app.get("/items", response_model=List[Item])
def read_items():
    with Session(engine) as session:
        items = session.exec(select(Item)).all()
        return items


# 3. GET /items/{item_id} — Return a specific item using its ID
@app.get("/items/{item_id}", response_model=Item)
def read_item(item_id: int):
    with Session(engine) as session:
        db_item = session.get(Item, item_id)
        if not db_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with ID {item_id} does not exist."
            )
        return db_item


# 4. PUT /items/{item_id} — Update the details/status of an existing item
@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: int, item_update: ItemUpdate):
    with Session(engine) as session:
        db_item = session.get(Item, item_id)
        if not db_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with ID {item_id} does not exist."
            )
        
        # Convert the update schema into a dictionary, excluding unset values
        update_data = item_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_item, key, value)
            
        session.add(db_item)
        session.commit()
        session.refresh(db_item)
        return db_item


# 5. DELETE /items/{item_id} — Delete an item report
@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int):
    with Session(engine) as session:
        db_item = session.get(Item, item_id)
        if not db_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with ID {item_id} does not exist."
            )
        session.delete(db_item)
        session.commit()
        return None  # HTTP 204 requires no content body


# 6. GET /items/status/{status} — Return items based on their status
@app.get("/items/status/{status}", response_model=List[Item])
def read_items_by_status(status: ItemStatus):
    with Session(engine) as session:
        items = session.exec(select(Item).where(Item.status == status)).all()
        return items


# 7. GET /items/category/{category} — Return all items belonging to a particular category
@app.get("/items/category/{category}", response_model=List[Item])
def read_items_by_category(category: str):
    with Session(engine) as session:
        # Case-insensitive query optimization can be applied depending on requirements
        items = session.exec(select(Item).where(Item.category == category)).all()
        return items
