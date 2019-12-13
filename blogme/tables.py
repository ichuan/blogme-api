#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/11

import datetime

import sqlalchemy as sa

metadata = sa.MetaData()


User = sa.Table(
    'user',
    metadata,
    sa.Column('id', sa.BigInteger, primary_key=True),
    sa.Column('username', sa.String(length=150), unique=True),
    sa.Column('password', sa.String(length=128)),
    sa.Column('email', sa.String(length=254)),
    sa.Column('is_active', sa.Boolean, default=True),
    sa.Column('is_superuser', sa.Boolean, default=False),
    sa.Column('last_login', sa.DateTime),
    sa.Column('date_joined', sa.DateTime, default=datetime.datetime.utcnow),
)

Article = sa.Table(
    'article',
    metadata,
    sa.Column('id', sa.BigInteger, primary_key=True),
    sa.Column('user_id', sa.ForeignKey(User.c.id), index=True),
    sa.Column('subject', sa.String(length=255)),
    sa.Column('content', sa.Text),
    # default arg: not supported by databases yet
    # https://github.com/encode/databases/issues/72
    sa.Column('created_at', sa.DateTime, default=datetime.datetime.utcnow),
)


if __name__ == '__main__':
    from sqlalchemy.sql import delete
    query = delete(Article).where(Article.c.id == 1).limit(1)
    print(query)
