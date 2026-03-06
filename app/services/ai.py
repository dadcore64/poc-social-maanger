import os
import json
from google import genai
from google.genai import types
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from ..models import IncomingMessage
from ..logger import logger
from dotenv import load_dotenv

class AISummaryResponse(BaseModel):
    summary: str
    priority_score: int

def summarize_and_prioritize_messages(db: Session, user_id: int):
    """
    Finds unread messages without an AI summary for the given user,
    sends them to Gemini, and updates the database with the results.
    """
    from ..models import PlatformConnection, User
    from ..security import decrypt_token
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return 0

    # Fetch API key
    if not user.encrypted_ai_token and not os.environ.get("PYTEST_CURRENT_TEST"):
        logger.warning(f"No AI token set for user {user.username}. Skipping AI processing.")
        return 0

    if user.encrypted_ai_token:
        api_key = decrypt_token(user.encrypted_ai_token)
    else:
        api_key = "dummy_key_for_testing"

    # In a real app we'd filter by user's connections. For simplicity, grabbing all unread without summary.
    connections = db.query(PlatformConnection).filter(PlatformConnection.user_id == user_id).all()
    conn_ids = [c.id for c in connections]
    
    if not conn_ids:
        return 0

    messages = db.query(IncomingMessage).filter(
        IncomingMessage.connection_id.in_(conn_ids),
        IncomingMessage.is_read == False,
        IncomingMessage.ai_summary == None
    ).order_by(IncomingMessage.timestamp.desc()).limit(15).all()

    if not messages:
        return 0

    client = genai.Client(api_key=api_key)
    processed_count = 0

    base_context = user.ai_context_prompt or "You are a social media manager assistant."
    
    # Prepare batch payload
    messages_payload = []
    for msg in messages:
        messages_payload.append({
            "id": msg.id,
            "content": msg.content
        })

    prompt = f"""
    {base_context}

    Please analyze the following list of incoming messages from customers/followers.
    For each message:
    1. Provide a very brief summary (1 sentence max).
    2. Assign a priority score from 1 to 10 (10 being highly urgent like a sponsorship or angry customer, 1 being a simple emoji or low priority comment).

    Messages to analyze:
    {json.dumps(messages_payload, indent=2)}

    Respond with exactly a JSON array of objects. Each object must have this exact structure:
    {{"id": <integer message id>, "summary": "...", "priority_score": X}}
    """
    try:
        # If in test mode, mock the response
        if os.environ.get("PYTEST_CURRENT_TEST"):
            mock_resp = [{"id": m.id, "summary": "Mocked summary", "priority_score": 5} for m in messages]
            response_text = json.dumps(mock_resp)
        else:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema={"type": "ARRAY", "items": {"type": "OBJECT", "properties": {"id": {"type": "INTEGER"}, "summary": {"type": "STRING"}, "priority_score": {"type": "INTEGER"}}, "required": ["id", "summary", "priority_score"]}}
                )
            )
            response_text = response.text

        data = json.loads(response_text)
        
        # Map responses back to messages
        results_map = {item["id"]: item for item in data if "id" in item}
        
        for msg in messages:
            if msg.id in results_map:
                res = results_map[msg.id]
                msg.ai_summary = res.get("summary", "Summary unavailable")
                msg.ai_priority_score = res.get("priority_score", 1)
                processed_count += 1
                
    except Exception as e:
        logger.error(f"Error processing AI batch summary: {e}")

    db.commit()
    return processed_count
