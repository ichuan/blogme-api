#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/13

import io
import logging
import logging.handlers
from datetime import datetime
from functools import partial
from typing import Tuple, Any
import xml.etree.ElementTree as ET
from contextlib import contextmanager
import email.utils

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


def get_rfc822_datetime(dt):
    return email.utils.format_datetime(dt)


def make_rss_xml(
    host,
    articles,
    title=None,
    desc=None,
    link_tpl='https://{host}/',
    url_tpl='https://{host}/#/p/{id}',
    feed_path='feed',
):
    '''
    spec: https://cyber.harvard.edu/rss/rss.html
    validator: https://validator.w3.org/feed/
    '''
    tb = ET.TreeBuilder()

    @contextmanager
    def tag_parent(name, attrs=None, data=None):
        tb.start(name, attrs or {})
        if data is not None:
            tb.data(data)
        yield
        tb.end(name)

    def tag(name, attrs=None, data=None):
        with tag_parent(name, attrs, data):
            pass

    with tag_parent(
        'rss', {'version': '2.0', 'xmlns:atom': 'http://www.w3.org/2005/Atom'}
    ):
        with tag_parent('channel'):
            website = link_tpl.format(host=host)
            tag('title', data=title or '')
            tag('link', data=website)
            tag('description', data=desc or '')
            if articles:
                _dt = get_rfc822_datetime(articles[0]['created_at'])
                tag('pubDate', data=_dt)
                tag('lastBuildDate', data=_dt)
            tag('generator', data='blogme')
            # refresh minutes
            tag('ttl', data=f'{60*24}')
            tag('atom:link', {'href': f'{website}{feed_path}', 'rel': 'self'})
            for i in articles:
                with tag_parent('item'):
                    url = url_tpl.format(host=host, id=i.id)
                    tag('title', data=i['subject'])
                    tag('link', data=url)
                    tag('description', data=i['content'])
                    tag('pubDate', data=get_rfc822_datetime(i['created_at']))
                    tag(
                        'dc:creator',
                        {'xmlns:dc': 'http://purl.org/dc/elements/1.1/'},
                        i['display_name'] or i['username'],
                    )
                    tag('guid', data=url)
    root = tb.close()
    with io.StringIO() as out:
        ET.ElementTree(root).write(out, encoding='unicode', xml_declaration=True)
        return out.getvalue()
