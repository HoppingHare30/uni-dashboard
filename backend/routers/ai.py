from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas, auth
from ..ai_service import query_gemini_chat

router = APIRouter(
    prefix="/ai",
    tags=["AI Assistant"]
)

@router.post("/chat", response_model=schemas.AIChatResponse)
def chat_with_assistant(
    chat_req: schemas.AIChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not chat_req.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty."
        )
        
    response_text, highlighted = query_gemini_chat(chat_req.query, db, current_user)
    return schemas.AIChatResponse(
        response=response_text,
        highlighted_widgets=highlighted
    )
