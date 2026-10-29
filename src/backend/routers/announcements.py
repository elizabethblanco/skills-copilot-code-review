"""Public and authenticated announcement endpoints."""

from datetime import date
from typing import Any, Dict, List, Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..database import announcements_collection
from .auth import get_authenticated_teacher

router = APIRouter(prefix="/announcements", tags=["announcements"])


class AnnouncementInput(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=2000)
    start_date: Optional[date] = None
    expiration_date: date


def serialize_announcement(announcement: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB's identifier and date strings to API-safe values."""
    announcement["id"] = str(announcement.pop("_id"))
    return announcement


def validate_announcement(data: AnnouncementInput) -> Dict[str, Any]:
    title = data.title.strip()
    message = data.message.strip()
    if not title or not message:
        raise HTTPException(status_code=422, detail="Title and message are required")
    if data.start_date and data.start_date > data.expiration_date:
        raise HTTPException(
            status_code=422,
            detail="Start date must be on or before the expiration date"
        )

    return {
        "title": title,
        "message": message,
        "start_date": data.start_date.isoformat() if data.start_date else None,
        "expiration_date": data.expiration_date.isoformat()
    }


def find_announcement(announcement_id: str) -> Dict[str, Any]:
    try:
        object_id = ObjectId(announcement_id)
    except InvalidId as error:
        raise HTTPException(status_code=404, detail="Announcement not found") from error

    announcement = announcements_collection.find_one({"_id": object_id})
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return announcement


@router.get("", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get announcements that are currently within their display dates."""
    today = date.today().isoformat()
    announcements = announcements_collection.find({
        "expiration_date": {"$gte": today},
        "$or": [
            {"start_date": {"$exists": False}},
            {"start_date": None},
            {"start_date": {"$lte": today}}
        ]
    }).sort("expiration_date", 1)
    return [serialize_announcement(item) for item in announcements]


@router.get("/manage", response_model=List[Dict[str, Any]])
def get_all_announcements(
    _teacher: Dict[str, Any] = Depends(get_authenticated_teacher)
) -> List[Dict[str, Any]]:
    """List all announcements for authenticated teachers."""
    announcements = announcements_collection.find().sort(
        [("expiration_date", 1), ("title", 1)]
    )
    return [serialize_announcement(item) for item in announcements]


@router.post("/manage", status_code=201)
def create_announcement(
    data: AnnouncementInput,
    _teacher: Dict[str, Any] = Depends(get_authenticated_teacher)
) -> Dict[str, Any]:
    """Create an announcement for authenticated teachers."""
    announcement = validate_announcement(data)
    result = announcements_collection.insert_one(announcement)
    announcement["id"] = str(result.inserted_id)
    return announcement


@router.put("/manage/{announcement_id}")
def update_announcement(
    announcement_id: str,
    data: AnnouncementInput,
    _teacher: Dict[str, Any] = Depends(get_authenticated_teacher)
) -> Dict[str, Any]:
    """Update an existing announcement for authenticated teachers."""
    existing = find_announcement(announcement_id)
    announcement = validate_announcement(data)
    announcements_collection.update_one(
        {"_id": existing["_id"]},
        {"$set": announcement}
    )
    announcement["id"] = announcement_id
    return announcement


@router.delete("/manage/{announcement_id}")
def delete_announcement(
    announcement_id: str,
    _teacher: Dict[str, Any] = Depends(get_authenticated_teacher)
) -> Dict[str, str]:
    """Delete an announcement for authenticated teachers."""
    existing = find_announcement(announcement_id)
    announcements_collection.delete_one({"_id": existing["_id"]})
    return {"message": "Announcement deleted"}
