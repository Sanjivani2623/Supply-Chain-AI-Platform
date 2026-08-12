from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.conversation import Conversation, Message
from app.schemas.supply_chain import ChatRequest
from app.services.agents.agent import run_agent_turn

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("")
def chat(payload: ChatRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    conversation = None
    if payload.conversation_id:
        conversation = db.query(Conversation).filter(Conversation.id == payload.conversation_id).first()
    if not conversation:
        conversation = Conversation(user_id=user.id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    db.add(Message(conversation_id=conversation.id, role="user", content=payload.message))
    db.commit()

    result = run_agent_turn(db, payload.message)

    db.add(Message(conversation_id=conversation.id, role="assistant", content=result["content"]))
    db.commit()

    return {
        "conversation_id": conversation.id,
        "response": result["content"],
        "tool_trace": result["tool_trace"],
    }
