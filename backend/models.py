from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    roll_number = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    borrowed_books = relationship("BorrowedBook", back_populates="user", cascade="all, delete-orphan")
    flagged_events = relationship("FlaggedEvent", back_populates="user", cascade="all, delete-orphan")
    liked_menu_days = relationship("LikedMenuDay", back_populates="user", cascade="all, delete-orphan")

class BorrowedBook(Base):
    __tablename__ = "borrowed_books"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(String, nullable=False)  # references the mock library book id
    title = Column(String, nullable=False)
    due_date = Column(String, nullable=False)  # ISO string or YYYY-MM-DD

    user = relationship("User", back_populates="borrowed_books")

class FlaggedEvent(Base):
    __tablename__ = "flagged_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(String, nullable=False)  # references the mock event id

    user = relationship("User", back_populates="flagged_events")

class LikedMenuDay(Base):
    __tablename__ = "liked_menu_days"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    day = Column(String, nullable=False)  # e.g., "Monday", "Tuesday"

    user = relationship("User", back_populates="liked_menu_days")

class AcademicPDF(Base):
    __tablename__ = "academic_pdfs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    uploaded_by = Column(String, nullable=False)  # Stores the name of student who uploaded
    file_data = Column(String, nullable=False)     # Base64-encoded PDF string
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)
