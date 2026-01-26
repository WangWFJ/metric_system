# =============================
# app/models/schemas.py —— 去除 user_id
# =============================
from pydantic import BaseModel, Field
from typing import Optional

class UserBase(BaseModel):
    username: str = Field(..., max_length=32)
    phone: Optional[str] = Field(None, max_length=11)
    role_id: Optional[int] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)

class AdminUserCreate(BaseModel):
    username: str = Field(..., max_length=32)
    password: Optional[str] = Field(None, max_length=128)
    phone: str = Field(..., min_length=11, max_length=11, pattern=r"^\d{11}$")
    role_id: int
    status: Optional[int] = Field(1, description="1正常 0锁定")

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, max_length=32)
    password: Optional[str] = Field(None, min_length=6, max_length=128)
    phone: Optional[str] = Field(None, max_length=11)
    role_id: Optional[int] = None
    status: Optional[int] = Field(None, description="1正常 0锁定")

class UserOut(UserBase):
    id: int
    status: int

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# class TokenData(BaseModel):
#     username: str
class TokenData(BaseModel):
    user_id: int


class IndicatorDataOut(BaseModel):
    indicator_id: int
    indicator_code: str
    indicator_name: str
    unit: Optional[str]
    is_positive: int
    value: Optional[float]
    benchmark: Optional[float]
    challenge: Optional[float]
    exemption: Optional[float]
    zero_tolerance: Optional[float]
    score: Optional[float]

    class Config:
        from_attributes = True

class ChangePassword(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

class UpdateMyProfile(BaseModel):
    phone: str | None = Field(None, min_length=11, max_length=11, pattern=r"^\d{11}$")
