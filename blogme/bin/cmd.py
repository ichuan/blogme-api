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

Options:
    -h --help         Show this screen
    --username=USER   Username [default: root]
    --password=PASS   Raw password for the user [default: R00t!]
'''


from docopt import docopt


def get_db():
    import sqlalchemy
    from blogme.settings import DATABASE_URL

    return sqlalchemy.create_engine(DATABASE_URL.replace('mysql', 'mysql+pymysql'))


def import_wordpress(xml_file):
    import re
    import os
    import uuid
    import urllib.request
    import xml.etree.ElementTree as ET
    from blogme.tables import User, Article
    from blogme.auth import hash_password
    from blogme import settings
    from sqlalchemy.sql import select, update

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
                email=i.find('wp:author_email', ns).text,
                display_name=i.find('wp:author_display_name', ns).text,
                is_superuser=bool(j == 0),
            )
        )
        username_to_id[username] = res.inserted_primary_key[0]
    # articles
    article_ids = []
    for i in tree.iter('item'.format(**ns)):
        res = conn.execute(
            Article.insert().values(
                subject=i.find('title', ns).text,
                content=i.find('content:encoded', ns).text,
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
        ext = url.rpartition('.')[-1]
        local_name = f'{uuid.uuid4()}.{ext}'
        local_path = dest_dir.joinpath(local_name)
        local_path_swp = f'{local_path}.swp'
        urllib.request.urlretrieve(url, local_path_swp)
        os.replace(local_path_swp, local_path)
        return f'<img src="{settings.MEDIA_URL}{local_name}" />'

    for pk in article_ids:
        print(f'Processing {pk}')
        content, *_ = conn.execute(
            select([Article.c.content]).select_from(Article).where(Article.c.id == pk)
        ).fetchone()
        content = re.sub(r'<img src="([^"]+)[^>]+>', download_image, content)
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
