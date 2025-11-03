"""
Database Schemas for Reiki Booking System

Each Pydantic model represents a MongoDB collection.
Class name (lowercased) is the collection name.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class Healer(BaseModel):
    """Healers available for booking"""
    name: str = Field(..., description="Healer full name", min_length=2, max_length=100)
    specialty: str = Field(..., description="Healing specialty (e.g., Usui Reiki, Crystal Reiki)", min_length=2)
    bio: Optional[str] = Field(None, description="Short bio or description", max_length=1000)
    email: Optional[EmailStr] = Field(None, description="Contact email")
    avatar_url: Optional[str] = Field(None, description="Profile image URL")
    rating: Optional[float] = Field(4.9, ge=0, le=5, description="Average rating")

class Booking(BaseModel):
    """Customer bookings for a specific healer"""
    customer_name: str = Field(..., description="Customer full name", min_length=2, max_length=100)
    customer_email: EmailStr = Field(..., description="Customer email")
    healer_id: str = Field(..., description="ID of the selected healer")
    notes: Optional[str] = Field(None, description="Optional notes or intentions", max_length=1000)
    scheduled_for: Optional[datetime] = Field(None, description="Requested date/time (optional)")
