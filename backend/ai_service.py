import os
import re
import json
import datetime
from sqlalchemy.orm import Session
from . import models

SYSTEM_INSTRUCTION = """
You are the AI Assistant for the Unified Campus Intelligence Dashboard.
You have access to 4 campus data sources (Library, Cafeteria, Events, Academics) and the authenticated user's profile data through the provided tools.
Your goal is to answer student queries accurately using ONLY the data returned from the tool calls.

CRITICAL RULES:
1. Do NOT fabricate, guess, or infer any factual details (e.g. book titles, menu items, event dates, room locations, or PDF titles) that are not explicitly returned by the tools.
2. If a tool call returns empty results or you cannot find any matching data, you must explicitly state that no results/data were found. Do NOT hallucinate names, dates, or menus.
3. Automatically use the user's profile data (borrowed books, flagged events, liked menu days) if they ask about "my" books, events, calendar, or schedule. Do not ask for their credentials or ID.
4. If the query requires combining data (e.g. finding events that don't clash with book due dates), call all relevant tools (like get_user_profile and list_events), compile the data, and filter it yourself.
5. In your response, write a natural-language summary.
6. At the end of your response, specify which widgets on the home screen are relevant to the query so they can be highlighted. To do this, include a JSON block at the very end of your message in this exact format:
```widget-highlight
["library", "cafeteria", "events", "academics", "calendar"]
```
Include only the widgets that were queried or are relevant to the user's question. Valid widget names are: "library", "cafeteria", "events", "academics", "calendar".
"""

def query_gemini_chat(query: str, db: Session, current_user: models.User) -> tuple[str, list[str]]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "AI assistant is currently unavailable — missing API configuration", []
        
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
    except ImportError:
        return "AI assistant is currently unavailable — google-generativeai not installed", []
    except Exception as e:
        return f"AI assistant is currently unavailable — Configuration error: {str(e)}", []
        
    # Define local tools in scope so they have access to db and current_user
    def get_user_profile() -> str:
        """Get the current logged-in user's profile details including borrowed books, flagged events, and liked menu days."""
        profile = {
            "name": current_user.name,
            "roll_number": current_user.roll_number,
            "email": current_user.email,
            "borrowed_books": [{"book_id": b.book_id, "title": b.title, "due_date": b.due_date} for b in current_user.borrowed_books],
            "flagged_events": [f.event_id for f in current_user.flagged_events],
            "liked_menu_days": [l.day for l in current_user.liked_menu_days]
        }
        return json.dumps(profile)
        
    def search_library(title_or_author: str) -> str:
        """Search books in the campus library by title or author. Returns a list of books matching the query."""
        from .routers.library import BOOKS
        q = title_or_author.lower()
        results = [b for b in BOOKS if q in b["title"].lower() or q in b["author"].lower()]
        return json.dumps(results)
        
    def get_book_availability(id_or_title: str) -> str:
        """Get the availability status of a book by its ID or title."""
        from .routers.library import BOOKS
        book = None
        for b in BOOKS:
            if b["id"] == id_or_title or b["title"].lower() == id_or_title.lower():
                book = b
                break
        if not book:
            return json.dumps({"error": "Book not found"})
        status_str = "Available" if book["available_copies"] > 0 else "Unavailable"
        return json.dumps({
            "id": book["id"],
            "title": book["title"],
            "available_copies": book["available_copies"],
            "status": status_str
        })
        
    def get_cafeteria_menu(day: str) -> str:
        """Get the cafeteria menu for a specific day (e.g. 'Monday', 'Tuesday', or 'today')."""
        from .routers.cafeteria import MENU, get_day_name
        matched_day = get_day_name(day)
        for entry in MENU:
            if entry["day"].lower() == matched_day.lower():
                return json.dumps(entry)
        return json.dumps({"error": f"Menu day '{day}' not found."})
        
    def get_full_cafeteria_menu() -> str:
        """Get the full 7-day cafeteria menu."""
        from .routers.cafeteria import MENU
        return json.dumps(MENU)
        
    def list_events(start_date: str = None, end_date: str = None) -> str:
        """List campus/club events. Optional start_date and end_date in YYYY-MM-DD format can be provided to filter events."""
        from .routers.events import EVENTS
        results = EVENTS
        if start_date:
            try:
                sd = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                results = [e for e in results if datetime.datetime.strptime(e["date"], "%Y-%m-%d").date() >= sd]
            except ValueError:
                return json.dumps({"error": "Invalid start_date format. Use YYYY-MM-DD"})
        if end_date:
            try:
                ed = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
                results = [e for e in results if datetime.datetime.strptime(e["date"], "%Y-%m-%d").date() <= ed]
            except ValueError:
                return json.dumps({"error": "Invalid end_date format. Use YYYY-MM-DD"})
        return json.dumps(results)
        
    def search_events(q: str) -> str:
        """Search campus/club events by club name or title."""
        from .routers.events import EVENTS
        query = q.lower()
        results = [e for e in EVENTS if query in e["title"].lower() or query in e["club"].lower()]
        return json.dumps(results)
        
    def search_academic_pdfs(q: str) -> str:
        """Search academic course textbooks and lecture PDFs by title or subject."""
        query = q.lower()
        pdfs = db.query(models.AcademicPDF).filter(
            (models.AcademicPDF.title.ilike(f"%{query}%")) | 
            (models.AcademicPDF.subject.ilike(f"%{query}%"))
        ).all()
        results = [{"id": p.id, "title": p.title, "subject": p.subject, "uploaded_by": p.uploaded_by, "upload_date": p.upload_date.isoformat()} for p in pdfs]
        return json.dumps(results)

    tools = [
        get_user_profile,
        search_library,
        get_book_availability,
        get_cafeteria_menu,
        get_full_cafeteria_menu,
        list_events,
        search_events,
        search_academic_pdfs
    ]

    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            tools=tools,
            system_instruction=SYSTEM_INSTRUCTION
        )
        
        chat = model.start_chat(enable_automatic_function_calling=True)
        response = chat.send_message(query)
        response_text = response.text
        
        # Parse highlighted widgets
        match = re.search(r"```widget-highlight\s*(.*?)\s*```", response_text, re.DOTALL)
        highlighted_widgets = []
        clean_response = response_text
        if match:
            try:
                highlighted_widgets = json.loads(match.group(1))
                clean_response = response_text.replace(match.group(0), "").strip()
            except Exception:
                pass
                
        return clean_response, highlighted_widgets
        
    except Exception as e:
        return f"AI assistant encountered an error while processing: {str(e)}", []
