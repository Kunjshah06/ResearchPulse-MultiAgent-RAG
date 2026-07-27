# =============================================================================
# PaperMind AI — User Authentication API Router
# =============================================================================
# Exposes signup, login, and profile status endpoints for Username & Password
# authentication using JWT tokens and SQLite database persistence.
# =============================================================================

from __future__ import annotations

import jwt
import time
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr, Field

from papermind.database.db_service import db_service
from papermind.core.logging.logger import get_logger

log = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

JWT_SECRET = "papermind-super-secret-key-2026-production-secure"
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 72


# ── Schemas ──────────────────────────────────────────────────────────────────

class SignUpRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    username_or_email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user: dict


# ── JWT Helpers ──────────────────────────────────────────────────────────────

def create_access_token(user_id: str, username: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "username": username,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid authorization token.")


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/signup", response_model=AuthResponse)
async def signup(req: SignUpRequest):
    """Registers a new user with Username, Email, and Password."""
    try:
        user = db_service.register_user(
            username=req.username,
            email=req.email,
            password=req.password,
        )
        token = create_access_token(user["id"], user["username"], user["email"])
        log.info("User registered successfully", username=user["username"])
        return {"token": token, "user": user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error("Signup failed", error=str(e))
        raise HTTPException(status_code=500, detail="Registration failed.")


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """Authenticates username/email and password credentials."""
    try:
        user = db_service.authenticate_user(
            username_or_email=req.username_or_email,
            password=req.password,
        )
        token = create_access_token(user["id"], user["username"], user["email"])
        log.info("User logged in successfully", username=user["username"])
        return {"token": token, "user": user}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        log.error("Login failed", error=str(e))
        raise HTTPException(status_code=500, detail="Authentication failed.")


@router.get("/me")
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Returns the logged-in user profile from Bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required.")

    token = authorization.split(" ")[1]
    payload = verify_access_token(token)

    user = db_service.get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found.")

    return {"user": user}


def get_user_from_auth_header(authorization: Optional[str]) -> Optional[Dict[str, Any]]:
    """Helper to extract user profile from Authorization header string."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        token = authorization.split(" ")[1]
        payload = verify_access_token(token)
        return db_service.get_user_by_id(payload["sub"])
    except Exception:
        return None
