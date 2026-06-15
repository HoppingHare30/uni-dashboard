from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from ..auth import get_current_user

router = APIRouter(
    prefix="/mcp/library",
    tags=["MCP Library"]
)

# Mock Dataset
BOOKS = [
    {"id": "lib-001", "title": "Introduction to Algorithms", "author": "Thomas H. Cormen", "category": "Computer Science", "total_copies": 5, "available_copies": 3},
    {"id": "lib-002", "title": "Design Patterns", "author": "Erich Gamma", "category": "Computer Science", "total_copies": 3, "available_copies": 0},
    {"id": "lib-003", "title": "Clean Code", "author": "Robert C. Martin", "category": "Computer Science", "total_copies": 10, "available_copies": 7},
    {"id": "lib-004", "title": "The Hobbit", "author": "J.R.R. Tolkien", "category": "Fiction", "total_copies": 4, "available_copies": 4},
    {"id": "lib-005", "title": "To Kill a Mockingbird", "author": "Harper Lee", "category": "Fiction", "total_copies": 2, "available_copies": 1},
    {"id": "lib-006", "title": "A Brief History of Time", "author": "Stephen Hawking", "category": "Science", "total_copies": 3, "available_copies": 2},
    {"id": "lib-007", "title": "Sapiens: A Brief History of Humankind", "author": "Yuval Noah Harari", "category": "History", "total_copies": 6, "available_copies": 5},
    {"id": "lib-008", "title": "Calculus Early Transcendentals", "author": "James Stewart", "category": "Mathematics", "total_copies": 8, "available_copies": 0},
    {"id": "lib-009", "title": "Artificial Intelligence: A Modern Approach", "author": "Stuart Russell", "category": "Computer Science", "total_copies": 5, "available_copies": 2},
    {"id": "lib-010", "title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "category": "Fiction", "total_copies": 4, "available_copies": 3}
]

@router.get("/books", response_model=List[dict])
def get_all_books(current_user: dict = Depends(get_current_user)):
    return BOOKS

@router.get("/search", response_model=List[dict])
def search_books(q: str, current_user: dict = Depends(get_current_user)):
    query = q.lower()
    results = [
        b for b in BOOKS
        if query in b["title"].lower() or query in b["author"].lower()
    ]
    return results

@router.get("/availability/{id_or_title}", response_model=dict)
def get_availability(id_or_title: str, current_user: dict = Depends(get_current_user)):
    book = None
    # Try searching by ID
    for b in BOOKS:
        if b["id"] == id_or_title:
            book = b
            break
    # Try searching by exact title (case-insensitive)
    if not book:
        for b in BOOKS:
            if b["title"].lower() == id_or_title.lower():
                book = b
                break

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    status_str = "Available" if book["available_copies"] > 0 else "Unavailable"
    return {
        "id": book["id"],
        "title": book["title"],
        "available_copies": book["available_copies"],
        "status": status_str
    }
