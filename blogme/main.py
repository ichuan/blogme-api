#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/10

from fastapi import FastAPI

from blogme import utils
from blogme.routers import users, articles


app = FastAPI()
database = utils.get_db()


@app.on_event('startup')
async def startup():
    await database.connect()


@app.on_event('shutdown')
async def shutdown():
    await database.disconnect()


app.include_router(users.router, prefix='/users', tags=['User'])
app.include_router(articles.router, prefix='/articles', tags=['Article'])
