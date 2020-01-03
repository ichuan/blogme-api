#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/12

'''
Usage:
    cmd.py create tables
    cmd.py drop tables
    cmd.py create superuser [--username=NAME] [--password=PASS]
    cmd.py changepassword <username> <password>
    cmd.py import wordpress <path_to_Wordpress.xml>
    cmd.py import djblog <path_to_dumped.json> [--urlprefix=URL]

Options:
    -h --help         Show this screen
    --username=USER   Username [default: root]
    --password=PASS   Raw password for the user [default: R00t!]
    --urlprefix=URL   Used for downloading original image
'''

import json

from docopt import docopt


def get_db():
    import sqlalchemy
    from blogme.settings import DATABASE_URL

    return sqlalchemy.create_engine(DATABASE_URL.replace('mysql', 'mysql+pymysql'))


def import_wordpress(xml_file):
    import re
    import uuid
    import urllib.request
    import xml.etree.ElementTree as ET
    from blogme.tables import User, Article
    from blogme.auth import hash_password
    from blogme import settings
    from sqlalchemy import select, update

    tree = ET.parse(xml_file)
    ns = dict(i[1] for i in ET.iterparse(xml_file, events=['start-ns']))
    if input('Confirm inserting wordpress data? [y/n] ') != 'y':
        return
    conn = get_db().connect()
    # users
    username_to_id = {}
    for j, i in enumerate(tree.iter('{{{wp}}}author'.format(**ns))):
        username = i.find('wp:author_login', ns).text
        res = conn.execute(
            User.insert().values(
                username=username,
                password=hash_password(username),
                email=i.find('wp:author_email', ns).text or '',
                display_name=i.find('wp:author_display_name', ns).text or '',
                is_superuser=bool(j == 0),
            )
        )
        username_to_id[username] = res.inserted_primary_key[0]
    # articles
    article_ids = []
    for i in tree.iter('item'.format(**ns)):
        res = conn.execute(
            Article.insert().values(
                subject=i.find('title', ns).text or '',
                content=i.find('content:encoded', ns).text or '',
                created_at=i.find('wp:post_date', ns).text,
                user_id=username_to_id[i.find('dc:creator', ns).text],
            )
        )
        article_ids.append(res.inserted_primary_key[0])
    print(f'Inserted {len(username_to_id)} users, {len(article_ids)} articles')
    # image
    print('Downloading images now...')
    dest_dir = settings.BASE_DIR.joinpath(settings.MEDIA_DIR)

    def download_image(obj):
        url = obj.group(1)
        if not url.startswith(('https://', 'http://')):
            return f'[未上传的图片]'
        ext = url.rpartition('.')[-1]
        local_name = f'{uuid.uuid4()}.{ext}'
        local_path = dest_dir.joinpath(local_name)
        urllib.request.urlretrieve(url, local_path)
        return f'<img src="{settings.MEDIA_URL}{local_name}" />'

    for pk in article_ids:
        print(f'Processing {pk}')
        content, *_ = conn.execute(
            select([Article.c.content]).select_from(Article).where(Article.c.id == pk)
        ).fetchone()
        content = re.sub(r'<img src="([^"]+)[^>]+>', download_image, content)
        conn.execute(update(Article).values(content=content).where(Article.c.id == pk))
    print('All done')


def import_djblog(json_file, url_prefix):
    '''
    ./manage.py dumpdata --indent=2 --natural > djblog.json
    '''
    import re
    import uuid
    import urllib.request
    from blogme.tables import User, Article
    from blogme import settings
    from blogme.auth import hash_password
    from sqlalchemy import select, update

    if not url_prefix:
        print('--urlprefix missing')
        return

    conn = get_db().connect()

    arr = json.load(open(json_file))
    users, articles = [], []
    # old => new
    user_id_map = {}
    for i in arr:
        if i['model'] == 'blog.post':
            j = i['fields']
            if len(j['title']) > 255:
                j['content'] += j['title']
                j['title'] = j['title'][:255]
            articles.append(
                {
                    'subject': j['title'],
                    'content': j['content'],
                    'created_at': j['created_at'],
                    'user_id': j['author'],
                }
            )
        elif i['model'] == 'auth.user':
            j = i['fields']
            users.append(
                {
                    'username': j['username'],
                    'display_name': j['username'],
                    'email': j['email'],
                    'password': hash_password(j['username']),
                    'is_superuser': True,
                    'last_login': j['last_login'],
                    'date_joined': j['date_joined'],
                    'old_id': i['pk'],
                }
            )
    articles.sort(key=lambda i: i['created_at'])
    users.sort(key=lambda i: i['old_id'])
    # users
    for u in users:
        old_id = u.pop('old_id')
        res = conn.execute(User.insert().values(**u))
        user_id_map[old_id] = res.inserted_primary_key[0]
    # articles
    article_ids = []
    for a in articles:
        a['user_id'] = user_id_map[a['user_id']]
        res = conn.execute(Article.insert().values(**a))
        article_ids.append(res.inserted_primary_key[0])
    print(f'Inserted {len(user_id_map)} users, {len(article_ids)} articles')
    # image
    print('Downloading images now...')
    dest_dir = settings.BASE_DIR.joinpath(settings.MEDIA_DIR)

    def download_image(obj):
        path = obj.group(1)
        url = f'{url_prefix}/{path}'
        if '.' in path:
            ext = path.rpartition('.')[-1]
        else:
            # random guess
            ext = 'jpg'
        local_name = f'{uuid.uuid4()}.{ext}'
        local_path = dest_dir.joinpath(local_name)
        urllib.request.urlretrieve(url, local_path)
        return f'<img src="{settings.MEDIA_URL}{local_name}" />'

    for pk in article_ids:
        print(f'Processing {pk}')
        content, *_ = conn.execute(
            select([Article.c.content]).select_from(Article).where(Article.c.id == pk)
        ).fetchone()
        content = re.sub(r'<img.+src="/([^"]+)[^>]+>', download_image, content)
        conn.execute(update(Article).values(content=content).where(Article.c.id == pk))
    print('All done')


if __name__ == '__main__':
    args = docopt(__doc__)

    if args['tables']:
        engine = get_db()
        from blogme.tables import metadata

        if args['create']:
            print('Creating tables...')
            metadata.create_all(engine)
        elif input('Confirm to drop tables?[y/n] ') == 'y':
            print('Dropping tables...')
            metadata.drop_all(engine)
    elif args['create'] and args['superuser']:
        from blogme.tables import User
        from blogme.auth import hash_password

        query = User.insert().values(
            username=args['--username'],
            password=hash_password(args['--password']),
            is_superuser=True,
        )
        res = get_db().connect().execute(query)
        print(f'Created superuser with id: {res.inserted_primary_key[0]}')
    elif args['changepassword']:
        from sqlalchemy import update
        from blogme.tables import User
        from blogme.auth import hash_password

        get_db().connect().execute(
            update(User)
            .where(User.c.username == args['<username>'])
            .values(password=hash_password(args['<password>']))
        )
        print(f'Password changed for {args["<username>"]}')
    elif args['import']:
        if args['wordpress']:
            import_wordpress(args['<path_to_Wordpress.xml>'])
        elif args['djblog']:
            import_djblog(args['<path_to_dumped.json>'], args['--urlprefix'])
