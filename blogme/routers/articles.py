#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/13

import uuid
import mimetypes
from typing import List

from fastapi import APIRouter, Depends, File, UploadFile, Header
from sqlalchemy import select, update, delete
from starlette.responses import Response

from blogme import settings, utils, auth
from blogme.tables import Article, User, KVStore
from blogme.models.article import (
    ArticleRead,
    ArticleCreate,
    ArticleUpdate,
    ArticleFile,
    ArticleArchiveRead,
)
from blogme.models.user import UserInDB


router = APIRouter()
database = utils.get_db()


async def is_article_belongs_to_user(article_id, user_id):
    row = await database.fetch_one(
        select([Article.c.id])
        .where(Article.c.id == article_id)
        .where(Article.c.user_id == user_id)
    )
    return bool(row)


@router.get('', response_model=List[ArticleRead])
async def article_list(params: dict = Depends(utils.list_params), user_id: int = None):
    query, need_reverse = utils.get_paged_query(Article, params)
    query = query.column(User.c.username).column(User.c.display_name)
    query = query.select_from(Article.join(User, Article.c.user_id == User.c.id))
    if user_id is not None:
        query = query.where(Article.c.user_id == user_id)
    rows = await database.fetch_all(query)
    if need_reverse:
        rows.reverse()
    return rows


@router.get('/archive', response_model=List[ArticleArchiveRead])
async def article_list_archive(
    params: dict = Depends(utils.list_params), user_id: int = None
):
    query, need_reverse = utils.get_paged_query(Article, params)
    query = query.column(User.c.username).column(User.c.display_name)
    query = query.select_from(Article.join(User, Article.c.user_id == User.c.id))
    if user_id is not None:
        query = query.where(Article.c.user_id == user_id)
    query = query.with_only_columns(
        [
            Article.c.id,
            Article.c.subject,
            Article.c.created_at,
            User.c.username,
            User.c.display_name,
        ]
    )
    rows = await database.fetch_all(query)
    if need_reverse:
        rows.reverse()
    return rows


@router.get(
    '/feed',
    responses={
        200: {
            'content': {
                'application/xml': {
                    'example': '<?xml version="1.0"?><rss version="2.0">...</rss>'
                }
            },
            'description': 'RSS XML',
        }
    },
)
async def article_list_feed(host: str = Header(None)):
    query = (
        select([Article, User.c.username, User.c.display_name])
        .select_from(Article.join(User, Article.c.user_id == User.c.id))
        .limit(10)
        .order_by(Article.c.id.desc())
    )
    rows = await database.fetch_all(query)
    # default site title and desc: site.name, site.desc in KVStore
    confs = {}
    query = select([KVStore]).where(KVStore.c.id.in_(('site.name', 'site.desc')))
    for r in await database.fetch_all(query):
        confs[r.id] = r.value
    xml = utils.make_rss_xml(
        host or 'localhost', rows, confs.get('site.name'), confs.get('site.desc')
    )
    return Response(content=xml, media_type='application/rss+xml; charset=utf-8')


@router.post('', response_model=ArticleRead)
async def article_create(
    article: ArticleCreate, user: UserInDB = Depends(auth.get_current_user)
):
    created_at = utils.now()
    spec = {
        'user_id': user.id,
        'subject': utils.sanitize_html(article.subject),
        'content': utils.sanitize_html(article.content),
        'created_at': created_at,
    }
    query = Article.insert().values(**spec)
    last_id = await database.execute(query)
    return {
        'id': last_id,
        'username': user.username,
        'display_name': user.display_name,
        **spec,
    }


@router.get('/{article_id}', response_model=ArticleRead)
async def article_detail(article_id: int):
    query = (
        select([Article, User.c.username, User.c.display_name])
        .where(Article.c.id == article_id)
        .select_from(Article.join(User, Article.c.user_id == User.c.id))
    )
    article = await database.fetch_one(query)
    if article:
        return article
    raise utils.HTTP400(detail='No such article')


@router.put('/{article_id}', response_model=ArticleUpdate)
async def article_update(
    article_id: int,
    article: ArticleUpdate,
    user: UserInDB = Depends(auth.get_current_user),
):
    spec = {
        'subject': utils.sanitize_html(article.subject),
        'content': utils.sanitize_html(article.content),
    }
    if user.is_superuser or await is_article_belongs_to_user(article_id, user.id):
        await database.execute(
            update(Article).where(Article.c.id == article_id).values(**spec)
        )
        return article
    raise utils.HTTP400(detail='No such article')


@router.delete('/{article_id}')
async def article_delete(
    article_id: int, user: UserInDB = Depends(auth.get_current_user)
):
    if user.is_superuser or await is_article_belongs_to_user(article_id, user.id):
        count = await database.execute(
            delete(Article).where(Article.c.id == article_id)
        )
        return {'success': bool(count)}
    raise utils.HTTP400(detail='No such article')


@router.post('/upload', response_model=ArticleFile)
async def upload_file(
    f: UploadFile = File(..., alias='file'),
    user: UserInDB = Depends(auth.get_current_user),
):
    dest_dir = settings.BASE_DIR.joinpath(settings.MEDIA_DIR)
    _, *exts = f.filename.rsplit('.', 1)
    if exts:
        ext = f'.{exts[0].lower()}'
    else:
        ext = mimetypes.guess_extension(f.content_type) or ''
    filename = f'{uuid.uuid4()}{ext}'
    await utils.save_uploaded_file(f, dest_dir.joinpath(filename))
    return {'url': f'{settings.MEDIA_URL}{filename}'}
