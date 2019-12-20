#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/10

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from blogme import utils, settings
from blogme.routers import users, articles, config


app = FastAPI(title='BlogMe API')
database = utils.get_db()


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
async def startup():
    await database.connect()


@app.on_event('shutdown')
async def shutdown():
    await database.disconnect()


app.include_router(config.router, prefix='/config', tags=['Config'])
app.include_router(users.router, prefix='/users', tags=['User'])
app.include_router(articles.router, prefix='/articles', tags=['Article'])
