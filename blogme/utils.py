#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/13

from datetime import datetime
from functools import partial

import databases
from fastapi import HTTPException

from blogme import settings


database = databases.Database(settings.DATABASE_URL)

HTTP400 = partial(HTTPException, status_code=400)
HTTP401 = partial(HTTPException, status_code=401)


def get_db():
    return database


def now():
    return datetime.utcnow()
