#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/20

from fastapi import APIRouter, Depends
from sqlalchemy import select, insert, update

from blogme import utils, auth
from blogme.models.user import UserInDB
from blogme.models.config import Config
from blogme.tables import KVStore


router = APIRouter()
database = utils.get_db()


@router.get('', response_model=dict)
async def config_list():
    return {i['id']: i['value'] for i in await database.fetch_all(select([KVStore]))}


@router.put('', response_model=dict)
async def config_upsert(
    config: Config, me: UserInDB = Depends(auth.get_current_user),
):
    if not me.is_superuser:
        raise utils.HTTP400(detail='Only superuser can change configs')
    try:
        await database.execute(
            insert(KVStore).values(id=config.key, value=config.value)
        )
    except Exception:
        await database.execute(
            update(KVStore).where(KVStore.c.id == config.key).values(value=config.value)
        )
    return {config.key: config.value}
