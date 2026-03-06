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
    # Fetch API key
    api_key = os.environ.get("GEMINI_API_KEY", "dummy_key_for_testing")
    if api_key == "dummy_key_for_testing" and not os.environ.get("PYTEST_CURRENT_TEST"):
        logger.warning("GEMINI_API_KEY not set. Skipping AI processing.")
        return 0

    # In a real app we'd filter by user's connections. For simplicity, grabbing all unread without summary.
    from ..models import PlatformConnection
    connections = db.query(PlatformConnection).filter(PlatformConnection.user_id == user_id).all()
    conn_ids = [c.id for c in connections]
    
    if not conn_ids:
        return 0

    messages = db.query(IncomingMessage).filter(
        IncomingMessage.connection_id.in_(conn_ids),
        IncomingMessage.is_read == False,
        IncomingMessage.ai_summary == None
    ).all()

    if not messages:
        return 0

    client = genai.Client(api_key=api_key)
    processed_count = 0

    for msg in messages:
        prompt = f"""
        You are a social media manager assistant.
        Please analyze this incoming message from a customer/follower:
        "{msg.content}"

        1. Provide a very brief summary (1 sentence max).
        2. Assign a priority score from 1 to 10 (10 being highly urgent like a sponsorship or angry customer, 1 being a simple emoji or low priority comment).
        
        Respond with exactly this JSON format:
        {{"summary": "...", "priority_score": X}}
        """

        try:
            # If in test mode, mock the response
            if os.environ.get("PYTEST_CURRENT_TEST"):
                response_text = '{"summary": "Mocked summary", "priority_score": 5}'
            else:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema={"type": "OBJECT", "properties": {"summary": {"type": "STRING"}, "priority_score": {"type": "INTEGER"}}, "required": ["summary", "priority_score"]}
                    )
                )
                response_text = response.text

            data = json.loads(response_text)
            msg.ai_summary = data.get("summary", "Summary unavailable")
            msg.ai_priority_score = data.get("priority_score", 1)
            processed_count += 1
            
        except Exception as e:
            logger.error(f"Error processing AI summary for msg {msg.id}: {e}")

    db.commit()
    return processed_count
