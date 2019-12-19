#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/13

import os
from datetime import datetime
from functools import partial
from typing import Tuple, Any

import aiofiles
import databases
from fastapi import HTTPException, Query
from sqlalchemy import select

from blogme import settings


database = databases.Database(settings.DATABASE_URL)

HTTP400 = partial(HTTPException, status_code=400)
HTTP401 = partial(HTTPException, status_code=401)

# 64KB
CHUNK_SIZE = 64 * 1024


def get_db():
    return database


def now():
    return datetime.utcnow()


async def save_uploaded_file(src_file, dest_path):
    await src_file.seek(0)
    tmp_path = f'{dest_path}.swp'
    async with aiofiles.open(tmp_path, 'wb+') as f:
        while True:
            data = await src_file.read(CHUNK_SIZE)
            if not data:
                break
            await f.write(data)
    os.replace(tmp_path, dest_path)


async def list_params(
    limit: int = Query(settings.PAGE_SIZE, ge=1, le=100),
    starting_after: int = Query(None, gt=0),
    ending_before: int = Query(None, gt=0),
):
    return {
        'limit': limit,
        'starting_after': starting_after,
        'ending_before': ending_before,
    }


def get_paged_query(table, params) -> Tuple[Any, bool]:
    '''
    returns (query, need_reverse)
    see #6
    '''
    query = select([table]).limit(params['limit'])
    need_reverse = False
    if params['ending_before']:
        need_reverse = True
        query = query.where(table.c.id > params['ending_before']).order_by(
            table.c.id.asc()
        )
    elif params['starting_after']:
        query = query.where(table.c.id < params['starting_after']).order_by(
            table.c.id.desc()
        )
    else:
        query = query.order_by(table.c.id.desc())
    return query, need_reverse
