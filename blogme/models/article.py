#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/13

import datetime

from pydantic import BaseModel, constr


class _Base(BaseModel):
    subject: constr(max_length=255)
    content: str


class ArticleCreate(_Base):
    pass


class ArticleInDB(_Base):
    id: int
    user_id: int
    created_at: datetime.datetime


class ArticleRead(ArticleInDB):
    username: constr(max_length=150)
    display_name: constr(max_length=150) = ''


class ArticleUpdate(_Base):
    pass


class ArticleFile(BaseModel):
    url: str
