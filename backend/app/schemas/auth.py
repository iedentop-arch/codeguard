"""
认证相关 Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token载荷"""
    sub: int  # user id
    exp: datetime
    role: str


class LoginRequest(BaseModel):
    """登录请求"""
    email: EmailStr
    password: str


class UserBase(BaseModel):
    """用户基础信息"""
    email: EmailStr
    name: str
    role: str


class UserCreate(UserBase):
    """创建用户"""
    password: str


class UserResponse(UserBase):
    """用户响应"""
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True