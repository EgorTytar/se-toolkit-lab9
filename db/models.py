"""SQLAlchemy database models for V2 features."""

import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    favorites = relationship("UserFavorite", back_populates="user", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")


class UserFavorite(Base):
    __tablename__ = "user_favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    driver_id = Column(String(50), nullable=True)
    constructor_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="favorites")


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    race_round = Column(Integer, nullable=False)
    race_year = Column(Integer, nullable=False)
    notify_before_hours = Column(Integer, default=2, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    method = Column(String(20), default="email", nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="reminders")


class RaceCache(Base):
    __tablename__ = "race_cache"

    year = Column(Integer, primary_key=True, nullable=False)
    round = Column(Integer, primary_key=True, nullable=False)
    race_name = Column(String(200), nullable=False)
    circuit = Column(String(200), nullable=False)
    date = Column(String(20), nullable=False)
    results_json = Column(Text, nullable=True)
    ai_summary_json = Column(Text, nullable=True)
    cached_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
