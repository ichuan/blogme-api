#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/13

import os
from datetime import datetime
from functools import partial

import aiofiles
import databases
from fastapi import HTTPException

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
