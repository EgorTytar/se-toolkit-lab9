"""Chat endpoints: manage AI chat sessions and messages."""

import datetime
import json
import logging
import re
import html
import urllib.request
import urllib.parse

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.database import get_db
from db.models import User, ChatSession, ChatMessage
from dependencies import get_current_user
from services.ai_assistant import AISummarizer
from services.ergast_client import ErgastClient
from services.data_parser import format_race_data

router = APIRouter(prefix="/api/chat", tags=["chat"])

ai_summarizer = AISummarizer()
ergast_client = ErgastClient()
logger = logging.getLogger(__name__)

# ── Security Constants ──
MAX_MESSAGE_LENGTH = 2000  # Max characters per message
MAX_SESSION_TITLE_LENGTH = 200
MAX_MESSAGES_PER_SESSION = 500  # Prevent runaway sessions
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 10  # messages per window per user

# Simple in-memory rate limiter
_rate_limit_store: dict[int, list[float]] = {}


def _check_rate_limit(user_id: int) -> None:
    """Simple sliding window rate limiter."""
    import time
    now = time.time()
    if user_id not in _rate_limit_store:
        _rate_limit_store[user_id] = []

    # Clean old entries
    _rate_limit_store[user_id] = [
        t for t in _rate_limit_store[user_id] if now - t < RATE_LIMIT_WINDOW
    ]

    if len(_rate_limit_store[user_id]) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Too many messages. Please wait a moment before sending another.",
        )

    _rate_limit_store[user_id].append(now)


def _sanitize_input(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not text:
        return ""

    # Truncate to max length
    text = text[:max_length]

    # Strip null bytes (prevent binary injection)
    text = text.replace("\x00", "")

    # Strip control characters except newlines and tabs
    text = re.sub(r'[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    return text.strip()


def _escape_for_prompt(text: str) -> str:
    """Escape text for use in AI system prompts to prevent prompt injection."""
    # HTML-escape to neutralize any injection attempts
    text = html.escape(text, quote=True)

    # Remove common prompt injection patterns
    injection_patterns = [
        r'(?i)ignore\s+previous\s+instructions',
        r'(?i)ignore\s+all\s+instructions',
        r'(?i)system\s*:',
        r'(?i)you\s+are\s+now',
        r'(?i)disregard\s+all\s+previous',
        r'(?i)forget\s+all\s+previous',
        r'(?i)new\s+instructions',
        r'(?i)override\s+instructions',
    ]
    for pattern in injection_patterns:
        text = re.sub(pattern, '[INJECTION BLOCKED]', text)

    return text


def _web_search(query: str, num_results: int = 3) -> str:
    """Search the web and return concise results for the AI to use."""
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; F1Assistant/1.0)'
            }
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')

        # Extract snippets from HTML
        import re
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
        results = []
        for s in snippets[:num_results]:
            # Strip HTML tags
            clean = re.sub(r'<[^>]+>', '', s).strip()
            if clean and len(clean) > 20:
                results.append(clean)
        return "\n".join(f"- {r}" for r in results) if results else ""
    except Exception as e:
        logger.warning(f"Web search failed: {e}")
        return ""


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
        title = _sanitize_input(str(body["title"]), max_length=MAX_SESSION_TITLE_LENGTH)
        if not title:
            title = "New Chat"

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


@router.post("/sessions/{session_id}/generate")
async def generate_response(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate AI response for the last user message in a session."""
    logger.info(f"generate_response called for session {session_id}, user {user.id}")
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id == session_id, ChatSession.user_id == user.id)
        .options(selectinload(ChatSession.messages))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.messages:
        raise HTTPException(status_code=400, detail="No messages in session")

    last_msg = session.messages[-1]
    if last_msg.role != "user":
        raise HTTPException(status_code=400, detail="Last message is not from user")

    # Build conversation context (last 20 messages)
    messages_context = []
    for m in session.messages[-20:]:
        messages_context.append({"role": m.role, "content": m.content})

    ai_content = await _generate_chat_response(last_msg.content, messages_context)

    ai_msg = ChatMessage(session_id=session_id, role="assistant", content=ai_content)
    db.add(ai_msg)
    session.updated_at = datetime.datetime.utcnow()
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


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: int,
    body: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message and get an AI response, or save only if save_only flag."""
    # Rate limiting
    _check_rate_limit(user.id)

    content = body.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message content is required")

    # Sanitize input
    content = _sanitize_input(content)
    if not content:
        raise HTTPException(status_code=400, detail="Message content is required")

    save_only = body.get("save_only", False)

    # Verify session ownership (prevents accessing other users' sessions)
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id == session_id, ChatSession.user_id == user.id)
        .options(selectinload(ChatSession.messages))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Prevent runaway sessions
    if len(session.messages) >= MAX_MESSAGES_PER_SESSION:
        raise HTTPException(
            status_code=400,
            detail="This chat has too many messages. Please start a new one.",
        )

    # Save user message (SQLAlchemy parameters prevent SQL injection)
    user_msg = ChatMessage(session_id=session_id, role="user", content=content)
    db.add(user_msg)
    await db.flush()

    # Auto-generate title from first message (sanitized and truncated)
    if session.title == "New Chat":
        session.title = _sanitize_input(content[:MAX_SESSION_TITLE_LENGTH])
        session.updated_at = datetime.datetime.utcnow()
        await db.flush()

    # If save_only, just return the saved message
    if save_only:
        await db.refresh(user_msg)
        return {
            "message": {
                "id": user_msg.id,
                "role": user_msg.role,
                "content": user_msg.content,
                "created_at": user_msg.created_at.isoformat(),
            }
        }

    # Build conversation context for AI (last 20 messages)
    # Escape all previous messages to prevent prompt injection from history
    messages_context = []
    for m in session.messages[-20:]:
        messages_context.append({
            "role": m.role,
            "content": _escape_for_prompt(m.content),
        })

    # Generate AI response (user message also escaped)
    ai_content = await _generate_chat_response(
        _escape_for_prompt(content),
        messages_context,
    )

    # Sanitize AI response before saving (prevent stored XSS)
    ai_content = _sanitize_input(ai_content, max_length=5000)

    # Save AI response
    ai_msg = ChatMessage(session_id=session_id, role="assistant", content=ai_content)
    db.add(ai_msg)
    session.updated_at = datetime.datetime.utcnow()
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
    """Generate an AI response using Qwen with verified F1 data."""
    current_year = datetime.datetime.now().year
    msg_lower = user_message.lower()

    context_parts = []

    # Always include current season standings with race count context
    races_completed = 0
    total_races = 0
    try:
        driver_standings = await ergast_client.get_driver_standings(current_year)
        if driver_standings:
            top5 = driver_standings[:5]
            parts = []
            for i, s in enumerate(top5):
                parts.append(f"{i+1}. {s['driver_name']} ({s['constructor']}) — {s['points']} pts, {s['wins']} wins")
            context_parts.append(
                f"**{current_year} Driver Standings (Top 5):**\n" + "\n".join(parts)
            )

        constructor_standings = await ergast_client.get_constructor_standings(current_year)
        if constructor_standings:
            top3 = constructor_standings[:3]
            parts = []
            for i, s in enumerate(top3):
                parts.append(f"{i+1}. {s['constructor']} — {s['points']} pts, {s['wins']} wins")
            context_parts.append(
                f"**{current_year} Constructor Standings (Top 3):**\n" + "\n".join(parts)
            )
    except Exception as e:
        logger.warning(f"Failed to fetch {current_year} standings: {e}")

    # Fetch completed races this season
    try:
        schedule = await ergast_client.get_season_schedule(current_year)
        if schedule:
            total_races = len(schedule)
            completed = [r for r in schedule if r.get("date") and r["date"] < datetime.datetime.now().strftime("%Y-%m-%d")]
            races_completed = len(completed)
            if races_completed < total_races:
                context_parts.append(
                    f"**IMPORTANT: The {current_year} season is ONGOING.** "
                    f"Only {races_completed} of {total_races} races have been completed so far. "
                    f"The championship has NOT been decided yet. "
                    f"Standings shown are the CURRENT provisional standings, not final results. "
                    f"NEVER say the championship 'was won' or 'has been won'. "
                    f"Always say 'currently leads' or 'is currently ahead in the standings'."
                )
            else:
                context_parts.append(
                    f"**{current_year} Season:** All {total_races} races completed. Championship decided."
                )
    except Exception as e:
        logger.warning(f"Failed to fetch {current_year} schedule: {e}")

    # Smart data fetching based on question keywords
    # Check for driver references
    driver_ids = ["verstappen", "norris", "leclerc", "hamilton", "piastri", "sainz",
                  "russell", "antonelli", "perez", "alonso", "gasly", "tsunoda",
                  "lawson", "albon", "hulkenberg", "bearman", "stroll", "ocon",
                  "bottas", "zhou", "magnussen", "colapinto", "hadjar", "doohan",
                  "max_verstappen", "lando_norris", "charles_leclerc", "lewis_hamilton",
                  "oscar_piastri", "carlos_sainz", "george_russell", "sergio_perez",
                  "fernando_alonso", "pierre_gasly", "yuki_tsunoda", "liam_lawson",
                  "alex_albon", "nico_hulkenberg", "oliver_bearman", "lance_stroll",
                  "esteban_ocon", "valtteri_bottas", "guanyu_zhou", "kevin_magnussen",
                  "franco_colapinto", "isack_hadjar", "jack_doohan"]

    found_drivers = [d for d in driver_ids if d.replace("_", " ") in msg_lower or d in msg_lower]

    for driver_id in found_drivers[:3]:  # Limit to 3 drivers
        try:
            info = await ergast_client.get_driver_info(driver_id)
            if info:
                context_parts.append(
                    f"**Driver: {info['given_name']} {info['family_name']}**\n"
                    f"  Code: {info.get('code', 'N/A')} | Nationality: {info.get('nationality', 'N/A')}\n"
                    f"  DOB: {info.get('date_of_birth', 'N/A')}"
                )
            # Get season results if a year is mentioned
            year_mentioned = None
            for y in range(current_year, 2015, -1):
                if str(y) in msg_lower:
                    year_mentioned = y
                    break
            if year_mentioned:
                results = await ergast_client.get_driver_season_results(driver_id, year_mentioned)
                if results:
                    wins = sum(1 for r in results if r.get("position") == "1")
                    podiums = sum(1 for r in results if str(r.get("position", "99")) in ["1", "2", "3"])
                    context_parts.append(
                        f"**{driver_id.replace('_', ' ').title()} {year_mentioned} Season:** "
                        f"{len(results)} races, {wins} wins, {podiums} podiums"
                    )
        except Exception as e:
            logger.warning(f"Failed to fetch driver {driver_id}: {e}")

    # Check for year mentions in question
    year_mentioned = None
    for y in range(current_year, 2000, -1):
        if str(y) in msg_lower:
            year_mentioned = y
            break

    if year_mentioned:
        try:
            standings = await ergast_client.get_driver_standings(year_mentioned)
            if standings:
                champion = standings[0]
                context_parts.append(
                    f"**{year_mentioned} World Champion:** {champion['driver_name']} "
                    f"({champion['constructor']}) — {champion['points']} pts, {champion['wins']} wins"
                )
        except Exception as e:
            logger.warning(f"Failed to fetch {year_mentioned} standings: {e}")

    # Check for circuit references
    circuit_keywords = ["monaco", "suzuka", "monza", "silverstone", "spa", "bahrain",
                        "interlagos", "cota", "hungaroring", "red_bull_ring",
                        "jeddah", "melbourne", "shanghai", "imola"]
    found_circuits = [c for c in circuit_keywords if c.replace("_", " ") in msg_lower or c in msg_lower]
    for circuit in found_circuits[:2]:
        try:
            results = await ergast_client.get_circuit_recent_results(circuit)
            if results:
                last_winner = results[0]
                context_parts.append(
                    f"**Last race at {circuit.replace('_', ' ').title()}:** "
                    f"{last_winner.get('driver_name', 'Unknown')} ({last_winner.get('constructor', '')}) — "
                    f"{last_winner.get('date', 'Unknown')}"
                )
        except Exception as e:
            logger.warning(f"Failed to fetch circuit {circuit}: {e}")

    # Check for "who won" + race/year questions
    if "who won" in msg_lower or "champion" in msg_lower or "standings" in msg_lower:
        if year_mentioned:
            try:
                standings = await ergast_client.get_driver_standings(year_mentioned)
                if standings:
                    top3 = standings[:3]
                    parts = []
                    for i, s in enumerate(top3):
                        parts.append(f"{i+1}. {s['driver_name']} ({s['constructor']}) — {s['points']} pts")
                    context_parts.append(
                        f"**{year_mentioned} Final Driver Standings:**\n" + "\n".join(parts)
                    )
            except Exception as e:
                logger.warning(f"Failed to fetch {year_mentioned} standings: {e}")

    # Build context
    context_text = "\n\n".join(context_parts) if context_parts else ""

    # If API data is insufficient, do a web search
    web_results = ""
    if not context_parts or len(context_parts) < 2:
        # Try to extract search keywords from the user's question
        search_query = f"F1 Formula 1 {user_message}"
        web_results = _web_search(search_query, num_results=3)
        if web_results:
            context_text += f"\n\n**Web search results for reference:**\n{web_results}"
            context_parts.append(web_results)

    if not context_text and not web_results:
        context_text = "\n\nNo specific F1 data or web results could be loaded for this question."

    system_prompt = (
        f"You are an F1 (Formula 1) expert assistant. The current year is {current_year}. "
        f"Answer the user's question with the best information available.\n\n"
        f"CRITICAL RULES:\n"
        f"1. If the {current_year} season is ONGOING (races completed < total races), NEVER say the championship 'was won' or 'has been won'. "
        f"   Always say 'currently leads the standings' or 'is currently ahead'.\n"
        f"2. ALWAYS try to answer — NEVER refuse with 'I don't have enough data'. Use the provided data first, then your general F1 knowledge.\n"
        f"3. Be specific with facts and data (positions, times, points, dates) whenever possible.\n"
        f"4. If you're unsure about a specific stat, say 'approximately' or 'around' rather than refusing.\n"
        f"5. Keep responses concise, engaging, and well-formatted with markdown.\n"
        f"6. Use a professional F1 commentator tone — engaging but accurate.\n\n"
        f"Here is the verified F1 data and web search results relevant to this question:\n{context_text}\n\n"
        f"Answer the question using this data and your F1 knowledge. Be helpful and confident."
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    try:
        response = await ai_summarizer.chat_response(messages)

        # Verification step: fact-check the AI response against real data
        verify_messages = [
            {"role": "system", "content": (
                f"You are a helpful fact-checker for an F1 assistant. "
                f"User question: \"{user_message}\"\n"
                f"Here is the AI's proposed answer:\n---\n{response}\n---\n"
                f"Here is the verified data from the official F1 database AND web search results:\n{context_text}\n\n"
                f"INSTRUCTIONS:\n"
                f"- If the {current_year} season is ONGOING, check that the answer does NOT say the championship 'was won' or 'has been won'. "
                f"  It must say 'currently leads' or 'is currently ahead'. If it says 'won', CORRECT it.\n"
                f"- Check that all explicit statistics (positions, points, wins, names, dates) match the verified data.\n"
                f"- If the answer contains clearly wrong numbers, correct them using the data.\n"
                f"- If the data doesn't have the exact info but the answer uses general F1 knowledge, that's fine — let it stand.\n"
                f"- NEVER remove answers just because they use general F1 knowledge.\n"
                f"- Only output the final answer — no explanations of what you changed.\n"
                f"- Use the same tone and format as the original answer."
            )},
        ]
        verified_response = await ai_summarizer.chat_response(verify_messages)
        return verified_response
    except Exception as e:
        return (
            f"I apologize, but I'm having trouble connecting to the AI service right now. "
            f"Please try again in a moment. (Error: {str(e)})"
        )
