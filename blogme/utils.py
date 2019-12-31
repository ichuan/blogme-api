#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/13

import logging
import logging.handlers
from datetime import datetime
from functools import partial
from typing import Tuple, Any

import aiofiles
import databases
import bleach
from fastapi import HTTPException, Query
from sqlalchemy import select

from blogme import settings


database = databases.Database(settings.DATABASE_URL)
logger = logging.getLogger('blogme')

HTTP400 = partial(HTTPException, status_code=400)
HTTP401 = partial(HTTPException, status_code=401)

# 64KB
CHUNK_SIZE = 64 * 1024
HTML_ALLOWED_TAGS = [
    'div',
    'p',
    'b',
    'i',
    'small',
    'u',
    'strike',
    'a',
    'li',
    'ul',
    'ol',
    'hr',
    'table',
    'tr',
    'td',
    'thead',
    'tbody',
    'th',
    'abbr',
    'blockquote',
    'code',
    'em',
    'strong',
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
    'br',
    'del',
    'pre',
    'figure',
    'img',
    'figcaption',
    'span',
]
HTML_ALLOWED_ATTRIBUTES = [
    'alt',
    'href',
    'title',
    'src',
    'width',
    'height',
    'class',
    'data-trix-attachment',
    'data-trix-content-type',
    'data-trix-attributes',
]


def get_db():
    return database


def now():
    return datetime.utcnow()


def setup_logging():
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    # 100MB
    handler = logging.handlers.RotatingFileHandler(
        filename=settings.LOG_FILE, maxBytes=104857600, backupCount=5,
    )
    handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s %(message)s'))
    logger.addHandler(handler)


async def save_uploaded_file(src_file, dest_path):
    await src_file.seek(0)
    async with aiofiles.open(dest_path, 'wb+') as f:
        while True:
            data = await src_file.read(CHUNK_SIZE)
            if not data:
                break
            await f.write(data)
    logger.info(f'Uploaded file: {dest_path}')


async def list_params(
    limit: int = Query(settings.PAGE_SIZE, ge=1, le=100),
    starting_after: int = Query(None, gt=0),
    ending_before: int = Query(None, gt=0),
):
    return {
        'limit': limit,
        'starting_after': starting_after,
        'ending_before': ending_before,
    }


def get_paged_query(table, params) -> Tuple[Any, bool]:
    '''
    returns (query, need_reverse)
    see #6
    '''
    query = select([table]).limit(params['limit'])
    need_reverse = False
    if params['ending_before']:
        need_reverse = True
        query = query.where(table.c.id > params['ending_before']).order_by(
            table.c.id.asc()
        )
    elif params['starting_after']:
        query = query.where(table.c.id < params['starting_after']).order_by(
            table.c.id.desc()
        )
    else:
        query = query.order_by(table.c.id.desc())
    return query, need_reverse


def sanitize_html(html):
    return bleach.clean(
        html,
        tags=bleach.sanitizer.ALLOWED_TAGS + HTML_ALLOWED_TAGS,
        attributes=HTML_ALLOWED_ATTRIBUTES,
    )
