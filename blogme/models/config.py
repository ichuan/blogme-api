#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/20

from pydantic import BaseModel, constr


class Config(BaseModel):
    key: constr(max_length=128)
    value: constr(max_length=255)
