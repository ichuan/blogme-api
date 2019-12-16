#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/13

from typing import List

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.sql import update, select, delete

from blogme import settings, utils, auth
from blogme.models.user import UserInDB, UserRead, UserCreate, UserUpdate
from blogme.models.token import Token
from blogme.tables import User, Article


router = APIRouter()
database = utils.get_db()


@router.get('/', response_model=List[UserRead])
async def user_list():
    query = select([User]).limit(settings.PAGE_SIZE).order_by(User.c.id.desc())
    return await database.fetch_all(query)


@router.post('/', response_model=UserRead)
async def create_user(user: UserCreate, me: UserInDB = Depends(auth.get_current_user)):
    if not me.is_superuser:
        raise utils.HTTP400(detail='Only superuser can create a user')
    spec = user.dict()
    spec.update(
        {
            'password': auth.hash_password(user.password),
            'is_active': True,
            'date_joined': utils.now(),
        }
    )
    try:
        async with database.transaction():
            last_id = await database.execute(User.insert().values(**spec))
            # unique username
            row = await database.fetch_one(
                select([func.count()])
                .select_from(User)
                .where(User.c.username == user.username)
            )
            assert row[0] == 1
            if user.email:
                # unique email
                row = await database.fetch_one(
                    select([func.count()])
                    .select_from(User)
                    .where(User.c.email == user.email)
                )
                assert row[0] == 1
            spec['id'] = last_id
    # blindly catch (pymysql.err.IntegrityError, AssertionError
    # cause IntegrityError is database independent
    except Exception:
        raise utils.HTTP400(detail='Username or email exists')
    return spec


@router.post('/access-token', response_model=Token)
async def create_access_token(form: OAuth2PasswordRequestForm = Depends()):
    user: UserInDB = await auth.authenticate_user(form.username, form.password)
    if not user:
        raise utils.HTTP400(detail='Invalid username or password')
    if not user.is_active:
        raise utils.HTTP400(detail='Inactive user')
    # update last_login
    await database.execute(
        update(User).where(User.c.id == user.id).values(last_login=utils.now())
    )
    return {
        'access_token': await auth.create_access_token(user),
        'token_type': 'bearer',
    }


@router.post('/test-token', response_model=UserRead)
async def test_access_token(me: UserInDB = Depends(auth.get_current_user)):
    return me


@router.put('/{user_id}', response_model=UserUpdate)
async def user_update(
    user_id: int, user: UserUpdate, me: UserInDB = Depends(auth.get_current_user)
):
    if me.id != user_id or not me.is_superuser:
        raise utils.HTTP400(detail='Cannot update other users')
    spec = {
        'username': user.username,
    }
    if user.password:
        spec['password'] = auth.hash_password(user.password)
    if user.email:
        spec['email'] = user.email
    if user.is_superuser is not None and me.is_superuser:
        spec['is_superuser'] = user.is_superuser
    try:
        async with database.transaction():
            await database.execute(
                update(User).where(User.c.id == user_id).values(**spec)
            )
            # ensure unique email
            if user.email:
                row = await database.fetch_one(
                    select([func.count()])
                    .select_from(User)
                    .where(User.c.email == user.email)
                )
                assert row[0] == 1
        return user
    except Exception:
        raise utils.HTTP400(detail='Username or email exists')


@router.delete('/{user_id}')
async def user_delete(user_id: int, me: UserInDB = Depends(auth.get_current_user)):
    if me.id == user_id:
        raise utils.HTTP400(detail='Cannot delete yourself')
    if not me.is_superuser:
        raise utils.HTTP400(detail='Cannot delete other users')
    # delete related articles
    await database.execute(delete(Article).where(Article.c.user_id == user_id))
    # delete user
    count = await database.execute(delete(User).where(User.c.id == user_id))
    return {'success': bool(count)}
