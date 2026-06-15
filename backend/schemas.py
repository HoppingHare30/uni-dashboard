from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
import datetime

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1)
    roll_number: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class BookBorrowRequest(BaseModel):
    book_id: str
    title: str
    due_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD format check

class BookBorrowResponse(BaseModel):
    id: int
    book_id: str
    title: str
    due_date: str

    class Config:
        from_attributes = True

class EventFlagRequest(BaseModel):
    event_id: str

class EventFlagResponse(BaseModel):
    id: int
    event_id: str

    class Config:
        from_attributes = True

class MenuLikeRequest(BaseModel):
    day: str

class MenuLikeResponse(BaseModel):
    id: int
    day: str

    class Config:
        from_attributes = True

class UserProfileResponse(BaseModel):
    id: int
    name: str
    roll_number: str
    email: str
    borrowed_books: List[BookBorrowResponse]
    flagged_events: List[EventFlagResponse]
    liked_menu_days: List[MenuLikeResponse]

    class Config:
        from_attributes = True

class AcademicPDFResponse(BaseModel):
    id: int
    title: str
    subject: str
    uploaded_by: str
    upload_date: datetime.datetime
    file_url: str

    class Config:
        from_attributes = True

class AIChatRequest(BaseModel):
    query: str

class AIChatResponse(BaseModel):
    response: str
    highlighted_widgets: List[str]
