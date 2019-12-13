#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/13

from fastapi import APIRouter, Depends

from blogme import utils, auth
from blogme.models.user import UserInDB, UserRead


router = APIRouter()
database = utils.get_db()


@router.get('/me', response_model=UserRead)
async def user_get_me(me: UserInDB = Depends(auth.get_current_user)):
    return me
