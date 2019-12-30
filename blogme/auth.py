#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/13

from typing import Optional
from datetime import datetime, timedelta

import jwt
from jwt import PyJWTError
from passlib.context import CryptContext
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from blogme import settings, utils
from blogme.models.user import UserInDB
from blogme.tables import User


pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
database = utils.get_db()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/users/access-token')


async def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    query = User.select(User.c.username == username)
    user_dict = await database.fetch_one(query=query)
    if user_dict:
        user = UserInDB(**user_dict)
        if verify_password(password, user.password):
            return user


async def create_access_token(user: UserInDB, expires: timedelta = None):
    if expires is None:
        expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    data = {
        'sub': user.id,
        'exp': datetime.utcnow() + expires,
    }
    return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def decode_access_token(token: str) -> Optional[UserInDB]:
    try:
        data = jwt.decode(token, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        uid: int = data.get('sub')
        if type(uid) is int and uid > 0:
            query = User.select(User.c.id == uid)
            user_dict = await database.fetch_one(query=query)
            if user_dict:
                return UserInDB(**user_dict)
    except PyJWTError:
        pass


def hash_password(password) -> str:
    return pwd_context.hash(password)


def verify_password(password, hashed) -> bool:
    try:
        return pwd_context.verify(password, hashed)
    except ValueError:
        return False


async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = await decode_access_token(token)
    if not user:
        raise utils.HTTP401(
            detail='Invalid authentication credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    if not user.is_active:
        raise utils.HTTP401(detail='Inactive user')
    return user
