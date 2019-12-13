#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/13

from pydantic import BaseModel


class Token(BaseModel):
    token_type: str
    access_token: str
