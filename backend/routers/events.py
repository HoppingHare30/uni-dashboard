import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from ..auth import get_current_user

router = APIRouter(
    prefix="/mcp/events",
    tags=["MCP Events"]
)

# Mock Events Dataset (10 events)
# Dates are structured near modern times or relative to now. We'll use absolute dates.
EVENTS = [
    {
        "id": "evt-001",
        "title": "AI Hackathon 2026",
        "club": "Coding Club",
        "date": "2026-06-16",
        "time": "09:00 AM",
        "location": "Main Auditorium & Lab 3",
        "description": "24-hour hackathon to build generative AI tools for campus life."
    },
    {
        "id": "evt-002",
        "title": "Intro to Robotics Workshop",
        "club": "Robotics Society",
        "date": "2026-06-17",
        "time": "02:00 PM",
        "location": "Robotics Lab",
        "description": "Learn the basics of Arduino programming and sensor integration."
    },
    {
        "id": "evt-003",
        "title": "Open Mic Poetry Night",
        "club": "Literary Club",
        "date": "2026-06-18",
        "time": "06:00 PM",
        "location": "Student Center Lounge",
        "description": "Express yourself through poems, stories, or spoken word performance."
    },
    {
        "id": "evt-004",
        "title": "Annual Campus Chess Tournament",
        "club": "Chess Club",
        "date": "2026-06-19",
        "time": "10:00 AM",
        "location": "Library Conference Room A",
        "description": "FIDE-rated Swiss system tournament for all skill levels."
    },
    {
        "id": "evt-005",
        "title": "Rock Concert Night",
        "club": "Music Society",
        "date": "2026-06-20",
        "time": "07:00 PM",
        "location": "Amphitheater",
        "description": "Live student rock bands performing original tracks and classic covers."
    },
    {
        "id": "evt-006",
        "title": "Startup Pitch Competition",
        "club": "Entrepreneurship Cell",
        "date": "2026-06-21",
        "time": "03:00 PM",
        "location": "Seminar Hall 2",
        "description": "Pitch your business idea to real investors and win seed funding."
    },
    {
        "id": "evt-007",
        "title": "Charity Coding Run",
        "club": "Rotaract Club",
        "date": "2026-06-22",
        "time": "08:00 AM",
        "location": "Campus Sports Complex",
        "description": "Run for a cause! Sponsorships go to local charity schools."
    },
    {
        "id": "evt-008",
        "title": "Photography Exhibition",
        "club": "Fine Arts Club",
        "date": "2026-06-23",
        "time": "11:00 AM",
        "location": "Campus Gallery",
        "description": "Stunning visuals captured by campus photographers on the theme 'Contrast'."
    },
    {
        "id": "evt-009",
        "title": "Debate Championship: AI & Future of Work",
        "club": "Debate Club",
        "date": "2026-06-24",
        "time": "04:00 PM",
        "location": "Auditorium 2",
        "description": "A heated debate on how AI will transform job markets."
    },
    {
        "id": "evt-010",
        "title": "Astronomy Stargazing Session",
        "club": "Science Club",
        "date": "2026-06-25",
        "time": "08:30 PM",
        "location": "Science Observatory Deck",
        "description": "Observe Jupiter's moons and Saturn's rings with our high-power telescope."
    }
]

@router.get("/all", response_model=List[dict])
def get_all_events(current_user: dict = Depends(get_current_user)):
    return EVENTS

@router.get("/list", response_model=List[dict])
def list_events(
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    current_user: dict = Depends(get_current_user)
):
    results = EVENTS
    
    if start_date:
        try:
            sd = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
        results = [e for e in results if datetime.datetime.strptime(e["date"], "%Y-%m-%d").date() >= sd]
        
    if end_date:
        try:
            ed = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
        results = [e for e in results if datetime.datetime.strptime(e["date"], "%Y-%m-%d").date() <= ed]
        
    return results

@router.get("/search", response_model=List[dict])
def search_events(q: str, current_user: dict = Depends(get_current_user)):
    query = q.lower()
    results = [
        e for e in EVENTS
        if query in e["title"].lower() or query in e["club"].lower()
    ]
    return results
