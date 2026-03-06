from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
import httpx

from ..database import get_db
from ..models import IncomingMessage, User
from ..security import decrypt_token
from ..logger import logger
from ..auth_deps import get_current_user_from_cookie

router = APIRouter(prefix="/api", tags=["messages"])

class ReplyRequest(BaseModel):
    content: str

@router.get("/messages")
def get_messages(hours: int = 1, db: Session = Depends(get_db), user: User = Depends(get_current_user_from_cookie)):
    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated")
        
    conn_ids = [c.id for c in user.platforms]
    if not conn_ids:
        return []
        
    from datetime import datetime, timedelta
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    messages = db.query(IncomingMessage).filter(IncomingMessage.connection_id.in_(conn_ids)).filter(IncomingMessage.timestamp >= cutoff_time).order_by(IncomingMessage.timestamp.desc()).all()
    result = []
    for msg in messages:
        platform_name = msg.platform.platform_name if msg.platform else "UNKNOWN"
        result.append({
            "id": msg.id,
            "platform": platform_name,
            "platform_custom_name": msg.platform.custom_name if msg.platform else None,
            "sender_name": msg.sender_name,
            "channel_name": msg.channel_name,
            "sender_avatar_url": msg.sender_avatar_url,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat() + ("Z" if "+" not in msg.timestamp.isoformat() else ""),
            "is_read": msg.is_read,
            "ai_summary": msg.ai_summary,
            "ai_priority_score": msg.ai_priority_score
        })
    return result


import json
from ..models import PlatformConnection

@router.post("/messages/sync")
async def sync_messages(platform: str = None, db: Session = Depends(get_db), user: User = Depends(get_current_user_from_cookie)):
    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated")
        
    query = db.query(PlatformConnection).filter(PlatformConnection.user_id == user.id)
    if platform and platform != "All Messages" and platform != "ALL":
        query = query.filter(PlatformConnection.platform_name == platform)
        
    connections = query.all()
    
    async with httpx.AsyncClient() as client:
        for conn in connections:
            if conn.platform_name == "DISCORD":
                if not conn.selected_channels:
                    continue
                try:
                    selected_channels = json.loads(conn.selected_channels)
                except json.JSONDecodeError:
                    continue
                    
                access_token = decrypt_token(conn.encrypted_token)
                if access_token in ("dummy_token", "xyz", "UNCHANGED") or not access_token:
                    continue
                    
                from datetime import datetime, timedelta
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                
                for channel_id in selected_channels:
                    base_url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=100"
                    headers = {"Authorization": f"Bot {access_token}"}
                    
                    # Fetch channel name
                    channel_name = "unknown"
                    try:
                        ch_resp = await client.get(f"https://discord.com/api/v10/channels/{channel_id}", headers=headers)
                        if ch_resp.status_code == 200:
                            channel_name = ch_resp.json().get("name", "unknown")
                    except Exception:
                        pass
                        
                    try:
                        last_msg_id = None
                        keep_fetching = True
                        
                        while keep_fetching:
                            url = base_url
                            if last_msg_id:
                                url += f"&before={last_msg_id}"
                                
                            resp = await client.get(url, headers=headers)
                            if resp.status_code == 200:
                                messages_data = resp.json()
                                if not messages_data:
                                    break
                                    
                                oldest_ts = datetime.utcnow()
                                
                                for msg_data in messages_data:
                                    ext_id = str(msg_data["id"])
                                    last_msg_id = ext_id
                                    
                                    # Parse Timestamp
                                    timestamp_str = msg_data.get("timestamp")
                                    try:
                                        ts = datetime.fromisoformat(timestamp_str).replace(tzinfo=None) if timestamp_str else datetime.utcnow()
                                    except Exception as e:
                                        logger.error(f"Timestamp parse error: {str(e)} - {timestamp_str}")
                                        ts = datetime.utcnow()
                                        
                                    oldest_ts = ts
                                    
                                    # Check if message already exists
                                    existing = db.query(IncomingMessage).filter(IncomingMessage.external_message_id == ext_id).first()
                                    if existing:
                                        # If it exists but is missing a channel name, update it
                                        if not existing.channel_name and channel_name != "unknown":
                                            existing.channel_name = channel_name
                                    else:
                                        # If it's a new message, create it
                                        author = msg_data.get("author", {})
                                        sender = author.get("username", "Unknown Discord User")
                                        author_id = author.get("id")
                                        avatar_hash = author.get("avatar")
                                        avatar_url = f"https://cdn.discordapp.com/avatars/{author_id}/{avatar_hash}.png" if author_id and avatar_hash else None
                                        content = msg_data.get("content", "")
                                        
                                        new_msg = IncomingMessage(
                                            connection_id=conn.id,
                                            external_message_id=ext_id,
                                            sender_name=sender,
                                            sender_avatar_url=avatar_url,
                                            content=content,
                                            timestamp=ts,
                                            channel_name=channel_name
                                        )
                                        db.add(new_msg)
                                        
                                if oldest_ts < thirty_days_ago:
                                    break
                            else:
                                logger.error(f"Discord API error: {resp.text}")
                                break
                    except Exception as e:
                        logger.error(f"Error fetching Discord channel {channel_id}: {str(e)}")
                        
                            
    db.commit()
    return {"status": "success"}


@router.post("/messages/{message_id}/reply")
async def reply_to_message(message_id: int, reply: ReplyRequest, db: Session = Depends(get_db)):
    msg = db.query(IncomingMessage).filter(IncomingMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    
    conn = msg.platform
    if not conn:
        raise HTTPException(status_code=400, detail="No platform connection found for this message")
        
    if conn.platform_name == "DISCORD":
        raise HTTPException(status_code=400, detail="Discord integration is read-only via webhooks")

    try:
        # Decrypt the stored API token to authenticate the outbound request
        access_token = decrypt_token(conn.encrypted_token)
        
        # Determine the correct API endpoint and payload structure based on the platform
        async with httpx.AsyncClient() as client:
            if conn.platform_name in ["INSTAGRAM", "FACEBOOK"]:
                # Example Meta Graph API call to send a reply
                url = f"https://graph.facebook.com/v19.0/me/messages"
                payload = {
                    "recipient": {"id": msg.external_message_id}, # In Meta, reply to the sender ID (which we might need to adjust based on exact Graph API requirements)
                    "message": {"text": reply.content}
                }
                headers = {"Authorization": f"Bearer {access_token}"}
                
                # In testing, we don't want to actually hit the real API if it's a dummy token
                if access_token != "dummy_token":
                    response = await client.post(url, json=payload, headers=headers)
                    if response.status_code >= 400:
                        logger.error(f"Meta API Error: {response.text}")
                        raise HTTPException(status_code=502, detail="Failed to send message to Meta")
            
            elif conn.platform_name == "YOUTUBE":
                # Example YouTube Data API v3 call to reply to a comment
                url = "https://www.googleapis.com/youtube/v3/comments"
                params = {"part": "snippet"}
                headers = {"Authorization": f"Bearer {access_token}"}
                payload = {
                    "snippet": {
                        "parentId": msg.external_message_id,
                        "textOriginal": reply.content
                    }
                }
                
                if access_token != "dummy_token":
                    response = await client.post(url, params=params, json=payload, headers=headers)
                    if response.status_code >= 400:
                        logger.error(f"YouTube API Error: {response.text}")
                        raise HTTPException(status_code=502, detail="Failed to send message to YouTube")
            
            else:
                raise HTTPException(status_code=400, detail="Unsupported platform for replies")

        # Mark as read once replied to
        msg.is_read = True
        db.commit()

        return {"status": "success", "message": "Reply sent successfully"}
    
    except Exception as e:
        logger.error(f"Error sending reply: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while sending the reply")
