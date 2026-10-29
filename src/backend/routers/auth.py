"""
Authentication endpoints for the High School Management System API
"""

from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..database import (
    auth_sessions_collection,
    teachers_collection,
    verify_password,
)

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)
bearer_scheme = HTTPBearer(auto_error=False)
SESSION_DURATION = timedelta(days=7)


def hash_session_token(token: str) -> str:
    """Hash an opaque session token before storing it."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_authenticated_teacher(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Dict[str, Any]:
    """Resolve a valid, unexpired bearer token to its teacher account."""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authentication required")

    session = auth_sessions_collection.find_one({
        "_id": hash_session_token(credentials.credentials),
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    teacher = teachers_collection.find_one({"_id": session["username"]})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return {
        "username": teacher["username"],
        "display_name": teacher["display_name"],
        "role": teacher["role"]
    }


@router.post("/login")
def login(username: str, password: str) -> Dict[str, Any]:
    """Login a teacher account"""
    # Find the teacher in the database
    teacher = teachers_collection.find_one({"_id": username})

    # Verify password using Argon2 verifier from database.py
    if not teacher or not verify_password(teacher.get("password", ""), password):
        raise HTTPException(
            status_code=401, detail="Invalid username or password")

    # Store only a hash so a database read cannot be used as a login token.
    access_token = secrets.token_urlsafe(32)
    auth_sessions_collection.insert_one({
        "_id": hash_session_token(access_token),
        "username": teacher["username"],
        "expires_at": datetime.now(timezone.utc) + SESSION_DURATION
    })

    # Return teacher information (excluding password)
    return {
        "username": teacher["username"],
        "display_name": teacher["display_name"],
        "role": teacher["role"],
        "access_token": access_token
    }


@router.get("/check-session")
def check_session(
    teacher: Dict[str, Any] = Depends(get_authenticated_teacher)
) -> Dict[str, Any]:
    """Check whether the bearer-token session is valid."""
    return teacher


@router.post("/logout")
def logout(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    teacher: Dict[str, Any] = Depends(get_authenticated_teacher)
) -> Dict[str, str]:
    """Revoke the current bearer-token session."""
    if credentials:
        auth_sessions_collection.delete_one({
            "_id": hash_session_token(credentials.credentials),
            "username": teacher["username"]
        })
    return {"message": "Logged out"}
