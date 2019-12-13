#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/13

import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    is_active: bool = True
    is_superuser: bool = False
    last_login: Optional[datetime.datetime] = None
    date_joined: datetime.datetime


class UserInDB(UserBase):
    id: int
    password: str


class UserRead(UserBase):
    pass


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    password: str
