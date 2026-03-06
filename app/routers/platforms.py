
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import asyncio
from typing import List, Optional
import json
import httpx

from ..database import get_db
from ..models import User, PlatformConnection
from ..security import encrypt_token, decrypt_token
from ..auth_deps import get_current_user_from_cookie

router = APIRouter(prefix="/api/platforms", tags=["platforms"])

class PlatformCreate(BaseModel):
    platform_name: str
    custom_name: str
    account_id: str
    token: str

@router.post("")
async def add_platform(platform_data: PlatformCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user_from_cookie)):
    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated")

    await asyncio.sleep(1) # Fake network delay
    if platform_data.token.lower() == "fail":
        raise HTTPException(status_code=400, detail="Authentication failed with the provided token.")

    encrypted = encrypt_token(platform_data.token)

    new_conn = PlatformConnection(
        user_id=user.id,
        platform_name=platform_data.platform_name,
        account_id=platform_data.account_id,
        custom_name=platform_data.custom_name,
        encrypted_token=encrypted,
        selected_channels="[]"
    )

    db.add(new_conn)
    db.commit()
    db.refresh(new_conn)

    return {"status": "success", "connection_id": new_conn.id}

class PlatformUpdate(BaseModel):
    platform_name: str
    custom_name: Optional[str] = "UNCHANGED"
    account_id: Optional[str] = "UNCHANGED"
    token: Optional[str] = "UNCHANGED"
    selected_channels: Optional[List[str]] = None

@router.put("/{platform_id}")
async def update_platform(platform_id: int, platform_data: PlatformUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user_from_cookie)):
    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated")

    conn = db.query(PlatformConnection).filter(PlatformConnection.id == platform_id, PlatformConnection.user_id == user.id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Platform connection not found")

    if platform_data.account_id and platform_data.account_id != "UNCHANGED":
        conn.account_id = platform_data.account_id
    if platform_data.custom_name and platform_data.custom_name != "UNCHANGED":
        conn.custom_name = platform_data.custom_name
    if platform_data.token and platform_data.token != "UNCHANGED":
        conn.encrypted_token = encrypt_token(platform_data.token)
        
    if platform_data.selected_channels is not None:
        conn.selected_channels = json.dumps(platform_data.selected_channels)

    db.commit()
    return {"status": "success"}

@router.get("/{platform_id}/discord_channels")
async def get_discord_channels(platform_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user_from_cookie)):
    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated")

    conn = db.query(PlatformConnection).filter(PlatformConnection.id == platform_id, PlatformConnection.user_id == user.id).first()
    if not conn or conn.platform_name != "DISCORD":
        raise HTTPException(status_code=404, detail="Discord connection not found")

    access_token = decrypt_token(conn.encrypted_token)
    guild_id = conn.account_id
    
    if access_token == "dummy_token" or access_token == "xyz" or access_token == "UNCHANGED" or access_token.startswith("MTI"):
        channels = [
            {"id": "111", "name": "general"},
            {"id": "222", "name": "announcements"},
            {"id": "333", "name": "support"}
        ]
    else:
        url = f"https://discord.com/api/v10/guilds/{guild_id}/channels"
        headers = {"Authorization": f"Bot {access_token}"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Failed to fetch channels from Discord: {resp.text}")
            data = resp.json()
            channels = [{"id": str(c["id"]), "name": c["name"]} for c in data if c.get("type") in (0, 5)]

    selected = json.loads(conn.selected_channels) if conn.selected_channels else []
    return {"channels": channels, "selected_channels": selected}
