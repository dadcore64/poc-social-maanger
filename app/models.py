from sqlalchemy import String, ForeignKey, DateTime, Boolean, func, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, Optional

from .database import Base

DEFAULT_AI_PROMPT = "You are a Growth Hacker and Social Media Marketing Expert. Your primary objective is to analyze incoming messages and identify marketing opportunities, lead generation potential, and avenues for brand growth. Ignore basic customer service or administrative requests unless they present a unique PR opportunity. Instead, look for signals of high intent, potential brand ambassadors, viral trends, user-generated content (UGC) opportunities, or strategic partnerships. Assign a priority score from 1 to 10, where 10 represents an immediate, high-value marketing or partnership opportunity, and 1 represents no marketing value."

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ai_provider: Mapped[Optional[str]] = mapped_column(String(50), default="gemini", nullable=True)
    encrypted_ai_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ai_context_prompt: Mapped[Optional[str]] = mapped_column(String, default=DEFAULT_AI_PROMPT, nullable=True)
    ai_min_length: Mapped[Optional[int]] = mapped_column(Integer, default=10, nullable=True)
    ai_stop_words: Mapped[Optional[str]] = mapped_column(String, default="thanks, thank you, great, awesome, love, first, haha, lol, yes, no, true", nullable=True)

    platforms: Mapped[List["PlatformConnection"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    discord_feeds: Mapped[List["DiscordFeed"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class PlatformConnection(Base):
    __tablename__ = "platform_connections"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    platform_name: Mapped[str] = mapped_column(String(50))
    account_id: Mapped[str] = mapped_column(String(255))
    encrypted_token: Mapped[str] = mapped_column(String(500))
    custom_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    selected_channels: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    user: Mapped["User"] = relationship(back_populates="platforms")
    messages: Mapped[List["IncomingMessage"]] = relationship(back_populates="platform", cascade="all, delete-orphan")

class IncomingMessage(Base):
    __tablename__ = "incoming_messages"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    connection_id: Mapped[int] = mapped_column(ForeignKey("platform_connections.id"))
    external_message_id: Mapped[str] = mapped_column(String(255), index=True)
    sender_name: Mapped[str] = mapped_column(String(255))
    sender_avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    content: Mapped[str] = mapped_column(String)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    channel_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    
    ai_summary: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ai_priority_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    platform: Mapped["PlatformConnection"] = relationship(back_populates="messages")

class DiscordFeed(Base):
    __tablename__ = "discord_feeds"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    webhook_url: Mapped[str] = mapped_column(String(500))
    server_name: Mapped[str] = mapped_column(String(255))
    channel_name: Mapped[str] = mapped_column(String(255))

    user: Mapped["User"] = relationship(back_populates="discord_feeds")

class AILog(Base):
    __tablename__ = "ai_logs"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    overall_summary: Mapped[str] = mapped_column(String)
    processed_count: Mapped[int] = mapped_column(Integer)
    filter_criteria: Mapped[str] = mapped_column(String)

    user: Mapped["User"] = relationship()

class MuteRule(Base):
    __tablename__ = "mute_rules"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    keyword: Mapped[str] = mapped_column(String(255))
    platform: Mapped[str] = mapped_column(String(50), nullable=True) # Optional: filter by platform

    user: Mapped["User"] = relationship()
