import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..auth import get_current_user

router = APIRouter(
    prefix="/mcp/cafeteria",
    tags=["MCP Cafeteria"]
)

# Mock 7-day Menu Dataset
MENU = [
    {
        "day": "Monday",
        "breakfast": "Aloo Paratha, Curd, Pickle, Tea",
        "lunch": "Rajma, Plain Rice, Roti, Seasonal Veg, Salad, Boondi Raita",
        "snacks": "Samosa, Mint Chutney, Chai",
        "dinner": "Paneer Bhurji / Egg Bhurji, Roti, Rice, Dal Fry"
    },
    {
        "day": "Tuesday",
        "breakfast": "Poha, Jalebi, Sprouts, Tea/Coffee",
        "lunch": "Kadhi Pakoda, Steamed Rice, Aloo Gobhi Dry, Roti, Papad",
        "snacks": "Bread Pakoda, Sweet Chutney, Tea",
        "dinner": "Butter Paneer / Chicken Masala, Butter Naan, Dal Makhani, Jeera Rice, Gulab Jamun"
    },
    {
        "day": "Wednesday",
        "breakfast": "Idli, Vada, Coconut Chutney, Sambar, Filter Coffee",
        "lunch": "Veg Pulao, Dal Tadka, Mix Veg Sabzi, Roti, Curd",
        "snacks": "Onion Pakoda, Masala Chai",
        "dinner": "Shahi Paneer / Fish Curry, Roti, Veg Pulao, Dal Fry, Sewai Kheer"
    },
    {
        "day": "Thursday",
        "breakfast": "Puri, Aloo Chana Masala, Suji Halwa, Chai",
        "lunch": "Chole Bhature, Onion Rings, Mint Raita, Papad",
        "snacks": "Pav Bhaji, Tea/Coffee",
        "dinner": "Soyabean Ki Sabzi, Roti, Plain Rice, Dal Tadka"
    },
    {
        "day": "Friday",
        "breakfast": "Veg Uttapam, Tomato Chutney, Sambar, Filter Coffee",
        "lunch": "Vegetable Biryani / Egg Biryani, Salan, Onion Raita, Salad",
        "snacks": "Dhokla, Green Chutney, Chai",
        "dinner": "Paneer Pasanda / Chicken Korma, Tandoori Roti, Veg Biryani, Vanilla Ice Cream"
    },
    {
        "day": "Saturday",
        "breakfast": "Bread Butter Jam, Scrambled Eggs, Tea/Coffee",
        "lunch": "Chana Masala, Roti, Rice, Cucumber Raita, Pickle",
        "snacks": "Bhel Puri, Lemonade / Nimbu Pani",
        "dinner": "Veg Manchurian Dry, Veg Hakka Noodles, Fried Rice, Tomato Soup"
    },
    {
        "day": "Sunday",
        "breakfast": "Masala Dosa, Tomato & Coconut Chutneys, Sambar, Tea",
        "lunch": "Special Veg Thali (Paneer Butter Masala, Dal Makhani, Jeera Rice, Baby Naan, Gulab Jamun)",
        "snacks": "Kachori, Chai",
        "dinner": "Egg Curry / Soyabean Pulao, Roti, Rice, Dal Fry"
    }
]

def get_day_name(query_day: str) -> str:
    cleaned = query_day.strip().lower()
    if cleaned == "today":
        # Get current weekday
        weekday = datetime.datetime.now().strftime("%A")
        return weekday
    elif cleaned == "tomorrow":
        weekday = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%A")
        return weekday
    
    # Otherwise match direct name
    days_map = {d.lower(): d for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
    return days_map.get(cleaned, query_day)

@router.get("/menu/all", response_model=List[dict])
def get_full_menu(current_user: dict = Depends(get_current_user)):
    return MENU

@router.get("/menu/{day}", response_model=dict)
def get_menu_by_day(day: str, current_user: dict = Depends(get_current_user)):
    matched_day = get_day_name(day)
    for entry in MENU:
        if entry["day"].lower() == matched_day.lower():
            return entry
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Menu day '{day}' not found. Valid days: Monday-Sunday, today, tomorrow."
    )
