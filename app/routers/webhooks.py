from fastapi import APIRouter, Depends, Request, HTTPException, BackgroundTasks, Response
from sqlalchemy.orm import Session
from datetime import datetime
import json
import hmac
import hashlib

from ..database import get_db
from ..models import PlatformConnection, IncomingMessage, MuteRule
from ..logger import logger

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# --- META (Facebook/Instagram) WEBHOOK ---
@router.get("/meta")
def verify_meta_webhook(request: Request):
    """
    Endpoint for Meta to verify the webhook URL during setup.
    Meta sends a hub.mode, hub.challenge, and hub.verify_token.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    # In production, this should match an environment variable
    VERIFY_TOKEN = "socialease_meta_verify_token"

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            logger.info("Meta webhook verified successfully.")
            return Response(content=challenge, media_type="text/plain")
        else:
            raise HTTPException(status_code=403, detail="Verification failed")
    raise HTTPException(status_code=400, detail="Missing parameters")

@router.post("/meta")
async def receive_meta_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Receives incoming message payloads from Meta.
    """
    # 1. (Optional but recommended) Verify X-Hub-Signature using App Secret
    payload = await request.json()
    logger.info(f"Received Meta Webhook Payload: {payload}")

    try:
        # Check if this is an Instagram or Facebook page payload
        if payload.get("object") in ["instagram", "page"]:
            for entry in payload.get("entry", []):
                # We need the recipient ID to map back to our user's PlatformConnection
                account_id = entry.get("id")
                
                # Check if we have a connection for this account
                conn = db.query(PlatformConnection).filter(
                    PlatformConnection.account_id == account_id,
                    PlatformConnection.platform_name.in_(["INSTAGRAM", "FACEBOOK"])
                ).first()

                if not conn:
                    logger.warning(f"Received webhook for unknown account ID: {account_id}")
                    continue

                for messaging in entry.get("messaging", []):
                    if "message" in messaging:
                        sender_id = messaging["sender"]["id"]
                        message_text = messaging["message"].get("text", "")
                        message_id = messaging["message"].get("mid")
                        timestamp = messaging.get("timestamp")

                        # Basic Mute Rule Check
                        mute_rules = db.query(MuteRule).filter(MuteRule.user_id == conn.user_id).all()
                        is_muted = any(rule.keyword.lower() in message_text.lower() for rule in mute_rules)

                        if not is_muted:
                            # Save to database
                            new_msg = IncomingMessage(
                                connection_id=conn.id,
                                external_message_id=message_id,
                                sender_name=f"MetaUser_{sender_id[-4:]}", # Usually you'd make an API call to get their real name
                                content=message_text,
                                timestamp=datetime.fromtimestamp(timestamp / 1000.0) if timestamp else datetime.utcnow()
                            )
                            db.add(new_msg)
            
            db.commit()
            return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing Meta webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing webhook")

# --- DISCORD WEBHOOK (Read-Only Catcher) ---
@router.post("/discord/{connection_id}")
async def receive_discord_payload(connection_id: int, request: Request, db: Session = Depends(get_db)):
    """
    A custom endpoint where users can point standard Discord Webhooks to stream channel data in.
    """
    payload = await request.json()
    
    conn = db.query(PlatformConnection).filter(
        PlatformConnection.id == connection_id,
        PlatformConnection.platform_name == "DISCORD"
    ).first()

    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    content = payload.get("content", "")
    sender = payload.get("username", "Discord User")
    msg_id = payload.get("id", f"ds_{int(datetime.utcnow().timestamp())}") # Discord webhooks don't always send IDs

    new_msg = IncomingMessage(
        connection_id=conn.id,
        external_message_id=msg_id,
        sender_name=sender,
        content=content
    )
    db.add(new_msg)
    db.commit()

    return {"status": "success"}
