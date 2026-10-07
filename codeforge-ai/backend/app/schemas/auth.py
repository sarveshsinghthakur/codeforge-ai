"""Pydantic schemas for authentication."""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional


class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def username_lower(cls, v: str) -> str:
        return v.lower()


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserRefreshRequest(BaseModel):
    refresh_token: str


class GoogleLoginRequest(BaseModel):
    credential: str = Field(..., min_length=20, max_length=4096)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: int
    public_id: str
    username: str
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    role: str
    is_active: bool
    preferred_language: str
    created_at: str

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=16000)
    bio: Optional[str] = Field(None, max_length=500)
    preferred_language: Optional[str] = Field(None, pattern=r"^(python|javascript|java|cpp|c)$")


class SubscriptionBrief(BaseModel):
    """Per-user subscription summary; fresh users default to plan 'free'."""
    active: bool = False
    plan: str = "free"        # free | admin | monthly | annual
    status: str = "free"      # free | pending | active | failed | expired
    expires_at: Optional[str] = None
    days_left: Optional[int] = None
    is_admin: bool = False


class AiChatsBrief(BaseModel):
    """Per-user AI usage summary; fresh users default to zeros."""
    conversations: int = 0
    messages: int = 0


class ProfileResponse(UserResponse):
    problems_solved: int = 0
    easy_solved: int = 0
    medium_solved: int = 0
    hard_solved: int = 0
    submission_count: int = 0
    acceptance_rate: float = 0.0
    subscription: SubscriptionBrief = Field(default_factory=SubscriptionBrief)
    ai_chats: AiChatsBrief = Field(default_factory=AiChatsBrief)


class GoogleLoginResponse(TokenResponse):
    user: UserResponse
