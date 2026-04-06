"""Chat endpoints: manage AI chat sessions and messages."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.database import get_db
from db.models import User, ChatSession, ChatMessage
from dependencies import get_current_user
from services.ai_assistant import AISummarizer

router = APIRouter(prefix="/api/chat", tags=["chat"])

ai_summarizer = AISummarizer()


# ── Chat Sessions ──


@router.get("/sessions")
async def list_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's chat sessions, most recently updated first."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
        }
        for s in sessions
    ]


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_session(
    body: dict = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new chat session."""
    title = "New Chat"
    if body and "title" in body:
        title = body["title"]

    session = ChatSession(user_id=user.id, title=title)
    db.add(session)
    await db.flush()
    await db.refresh(session)

    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a session with all its messages."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id == session_id, ChatSession.user_id == user.id)
        .options(selectinload(ChatSession.messages))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            }
            for m in session.messages
        ],
    }


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a session and all its messages."""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id, ChatSession.user_id == user.id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.execute(delete(ChatSession).where(ChatSession.id == session_id))
    await db.flush()


# ── Chat Messages ──


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: int,
    body: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message and get an AI response."""
    content = body.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message content is required")

    # Verify session ownership
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id == session_id, ChatSession.user_id == user.id)
        .options(selectinload(ChatSession.messages))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save user message
    user_msg = ChatMessage(session_id=session_id, role="user", content=content)
    db.add(user_msg)
    await db.flush()

    # Auto-generate title from first message
    if session.title == "New Chat":
        session.title = content[:50] + ("..." if len(content) > 50 else "")
        session.updated_at = datetime.utcnow()

    # Build conversation context for AI (last 20 messages)
    messages_context = []
    for m in session.messages[-20:]:
        messages_context.append({"role": m.role, "content": m.content})

    # Generate AI response
    ai_content = await _generate_chat_response(content, messages_context)

    # Save AI response
    ai_msg = ChatMessage(session_id=session_id, role="assistant", content=ai_content)
    db.add(ai_msg)
    session.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(session)
    await db.refresh(ai_msg)

    return {
        "message": {
            "id": ai_msg.id,
            "role": ai_msg.role,
            "content": ai_msg.content,
            "created_at": ai_msg.created_at.isoformat(),
        }
    }


async def _generate_chat_response(user_message: str, conversation_history: list) -> str:
    """Generate an AI response using Qwen with F1 context."""
    system_prompt = (
        "You are an F1 (Formula 1) expert assistant. You have access to real F1 data "
        "from the Ergast/Jolpica-F1 API. Answer questions about drivers, races, circuits, "
        "seasons, and championship history. Be specific with facts and data when possible. "
        "If you don't know something or it can't be verified from real data, say so clearly. "
        "Never hallucinate race results, driver names, or statistics. "
        "Keep responses concise and engaging. Use markdown formatting when helpful."
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    try:
        response = await ai_summarizer.chat_response(messages)
        return response
    except Exception as e:
        return (
            f"I apologize, but I'm having trouble connecting to the AI service right now. "
            f"Please try again in a moment. (Error: {str(e)})"
        )
