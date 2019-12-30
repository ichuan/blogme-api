#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/11

import os
import pathlib


BASE_DIR = pathlib.Path(__file__).resolve().parent

DATABASE_USER = os.getenv('DB_USER', 'root')
DATABASE_PASS = os.getenv('DB_PASS', '')
DATABASE_HOST = os.getenv('DB_HOST', 'localhost')
DATABASE_NAME = os.getenv('DB_NAME', 'blogme')

DATABASE_URL = (
    f'mysql://{DATABASE_USER}:{DATABASE_PASS}@{DATABASE_HOST}'
    f'/{DATABASE_NAME}?charset=utf8mb4'
)

PAGE_SIZE = 10

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(32).hex())
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 60 * 24))

MEDIA_DIR = 'public/upload/'
MEDIA_URL = '/public/upload/'

CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(' ')
