#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/13

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from blogme import utils, auth
from blogme.models.user import UserInDB, UserRead
from blogme.models.token import Token


router = APIRouter()
database = utils.get_db()


@router.post('/access-token', response_model=Token)
async def create_access_token(form: OAuth2PasswordRequestForm = Depends()):
    user: UserInDB = await auth.authenticate_user(form.username, form.password)
    if not user:
        raise utils.HTTP400(detail='Invalid username or password')
    if not user.is_active:
        raise utils.HTTP400(detail='Inactive user')
    return {
        'access_token': await auth.create_access_token(user),
        'token_type': 'bearer'
    }


@router.post('/test-token', response_model=UserRead)
async def test_access_token(me: UserInDB = Depends(auth.get_current_user)):
    return me
