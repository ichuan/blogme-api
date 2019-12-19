#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/13

import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class _Base(BaseModel):
    '''
    DB, Create, Update 三状态下共享的字段
    '''

    username: str
    display_name: str = None
    email: Optional[EmailStr] = None
    is_superuser: bool = False


class UserRead(_Base):
    id: int
    is_active: bool = True
    last_login: Optional[datetime.datetime] = None
    date_joined: datetime.datetime


class UserInDB(UserRead):
    password: str


class UserCreate(_Base):
    password: str


class UserUpdate(_Base):
    password: Optional[str]
