#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/13

import mimetypes
from typing import List

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.sql import select, update, delete

from blogme import settings, utils, auth
from blogme.tables import Article
from blogme.models.article import (
    ArticleRead,
    ArticleCreate,
    ArticleUpdate,
    ArticleFile,
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


@router.get('/', response_model=List[ArticleRead])
async def article_list():
    query = select([Article]).limit(settings.PAGE_SIZE).order_by(Article.c.id.desc())
    return await database.fetch_all(query)


@router.post('/', response_model=ArticleRead)
async def article_create(
    article: ArticleCreate, user: UserInDB = Depends(auth.get_current_user)
):
    created_at = utils.now()
    spec = {
        'user_id': user.id,
        'subject': article.subject,
        'content': article.content,
        'created_at': created_at,
    }
    query = Article.insert().values(**spec)
    last_id = await database.execute(query)
    return {
        'id': last_id,
        **spec,
    }


@router.get('/{article_id}', response_model=ArticleRead)
async def article_detail(article_id: int):
    article = await database.fetch_one(Article.select(Article.c.id == article_id))
    if article:
        return article
    raise utils.HTTP400(detail='No such article')


@router.put('/{article_id}', response_model=ArticleUpdate)
async def article_update(
    article_id: int,
    article: ArticleUpdate,
    user: UserInDB = Depends(auth.get_current_user),
):
    if await is_article_belongs_to_user(article_id, user.id):
        await database.execute(
            update(Article).where(Article.c.id == article_id).values(**article.dict())
        )
        return article
    raise utils.HTTP400(detail='No such article')


@router.delete('/{article_id}')
async def article_delete(
    article_id: int, user: UserInDB = Depends(auth.get_current_user)
):
    if await is_article_belongs_to_user(article_id, user.id):
        count = await database.execute(
            delete(Article).where(Article.c.id == article_id)
        )
        return {'success': bool(count)}
    raise utils.HTTP400(detail='No such article')


@router.post('/upload/file', response_model=ArticleFile)
async def upload_file(
    f: UploadFile = File(...), user: UserInDB = Depends(auth.get_current_user)
):
    dest_dir = settings.BASE_DIR.joinpath(settings.MEDIA_DIR)
    _, *exts = f.filename.rsplit('.', 1)
    if exts:
        ext = f'.{exts[0].lower()}'
    else:
        ext = mimetypes.guess_extension(f.content_type) or ''
    filename = f'{utils.random_hex()}{ext}'
    await utils.save_uploaded_file(f, dest_dir.joinpath(filename))
    return {'url': f'{settings.MEDIA_URL}{filename}'}
