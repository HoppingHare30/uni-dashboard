import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import models, schemas, auth
from .events import EVENTS  # To resolve event details

router = APIRouter(
    prefix="/profile",
    tags=["Profile & Calendar"]
)

@router.get("/me", response_model=schemas.UserProfileResponse)
def get_my_profile(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# --- Borrowed Books ---
@router.post("/books", response_model=schemas.BookBorrowResponse, status_code=status.HTTP_201_CREATED)
def add_borrowed_book(
    book_data: schemas.BookBorrowRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Validate due date is not in the past
    try:
        due_date_obj = datetime.datetime.strptime(book_data.due_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid due date format. Use YYYY-MM-DD."
        )

    if due_date_obj < datetime.date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Due date must be today or later."
        )

    # Check if already borrowed
    existing = db.query(models.BorrowedBook).filter(
        models.BorrowedBook.user_id == current_user.id,
        models.BorrowedBook.book_id == book_data.book_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This book is already in your borrowed list."
        )

    db_book = models.BorrowedBook(
        user_id=current_user.id,
        book_id=book_data.book_id,
        title=book_data.title,
        due_date=book_data.due_date
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@router.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_borrowed_book(
    book_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_book = db.query(models.BorrowedBook).filter(
        models.BorrowedBook.user_id == current_user.id,
        models.BorrowedBook.book_id == book_id
    ).first()
    
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Borrowed book entry not found."
        )
        
    db.delete(db_book)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# --- Flagged Events ---
@router.post("/events", response_model=schemas.EventFlagResponse)
def toggle_flag_event(
    event_data: schemas.EventFlagRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    existing = db.query(models.FlaggedEvent).filter(
        models.FlaggedEvent.user_id == current_user.id,
        models.FlaggedEvent.event_id == event_data.event_id
    ).first()

    if existing:
        # Unflag it
        db.delete(existing)
        db.commit()
        # Return empty/dummy or some indicating message, let's raise a 204 or return a detail.
        # But schemas.EventFlagResponse is expected. So let's return it with deleted flag context.
        # Or we can just return a custom message. But since we need to match the return schema,
        # let's return the deleted model info.
        return existing
    
    # Flag it
    db_event = models.FlaggedEvent(
        user_id=current_user.id,
        event_id=event_data.event_id
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

# --- Liked Cafeteria Days ---
@router.post("/cafeteria", response_model=schemas.MenuLikeResponse)
def toggle_like_menu_day(
    menu_data: schemas.MenuLikeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    matched_day = None
    for d in valid_days:
        if d.lower() == menu_data.day.strip().lower():
            matched_day = d
            break
            
    if not matched_day:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid day: '{menu_data.day}'. Valid days: Monday to Sunday."
        )

    existing = db.query(models.LikedMenuDay).filter(
        models.LikedMenuDay.user_id == current_user.id,
        models.LikedMenuDay.day == matched_day
    ).first()

    if existing:
        # Unlike it
        db.delete(existing)
        db.commit()
        return existing

    # Like it
    db_like = models.LikedMenuDay(
        user_id=current_user.id,
        day=matched_day
    )
    db.add(db_like)
    db.commit()
    db.refresh(db_like)
    return db_like

# --- Calendar Aggregation ---
def get_date_for_weekday(day_name: str) -> datetime.date:
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    try:
        target_idx = days.index(day_name.lower())
    except ValueError:
        return datetime.date.today()
    today = datetime.date.today()
    current_idx = today.weekday()
    diff = target_idx - current_idx
    return today + datetime.timedelta(days=diff)

@router.get("/calendar", response_model=List[dict])
def get_personal_calendar(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    calendar_items = []
    
    # 1. Borrowed Books Due Dates
    for b in current_user.borrowed_books:
        calendar_items.append({
            "type": "book_due",
            "title": f"Book Due: {b.title}",
            "date": b.due_date,
            "reference_id": b.book_id,
            "description": f"Return deadline for '{b.title}' borrowed from Library."
        })
        
    # 2. Flagged Events
    # Map event ID to event details
    events_map = {e["id"]: e for e in EVENTS}
    for f in current_user.flagged_events:
        evt = events_map.get(f.event_id)
        if evt:
            calendar_items.append({
                "type": "event",
                "title": evt["title"],
                "date": evt["date"],
                "reference_id": evt["id"],
                "description": f"Club: {evt['club']} | Time: {evt['time']} | Location: {evt['location']}"
            })
            
    # 3. Liked Menu Days (mapped to date in current week)
    for l in current_user.liked_menu_days:
        liked_date = get_date_for_weekday(l.day)
        calendar_items.append({
            "type": "liked_menu",
            "title": f"Liked Menu: {l.day}",
            "date": liked_date.isoformat(),
            "reference_id": l.day,
            "description": f"Your liked menu day! Check cafeteria widget for today's special."
        })
        
    # Sort chronologically
    calendar_items.sort(key=lambda x: x["date"])
    return calendar_items
