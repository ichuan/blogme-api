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

DATABASE_URL = f'mysql://{DATABASE_USER}:{DATABASE_PASS}@{DATABASE_HOST}/{DATABASE_NAME}?charset=utf8mb4'

PAGE_SIZE = 10

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = 'bab1cc1dc350b5a2c5d296ba024b762fa32aafe5fa7861d670565d6bb5be8279'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

MEDIA_DIR = 'public/upload/'
MEDIA_URL = '/public/upload/'

CORS_ORIGINS = [
    'http://localhost:3000',
    'https://yanxinyi.me',
    'https://yanyichen.com',
    'https://52mandy.com',
    'https://ichuan.net',
]
