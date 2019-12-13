#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/13

import datetime

from pydantic import BaseModel


class ArticleBase(BaseModel):
    subject: str
    content: str


class ArticleCreate(ArticleBase):
    pass


class ArticleInDB(ArticleBase):
    id: int
    user_id: int
    created_at: datetime.datetime


class ArticleRead(ArticleInDB):
    pass


class ArticleUpdate(ArticleBase):
    pass
