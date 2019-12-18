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
    import xml.etree.ElementTree as ET

    tree = ET.parse(xml_file)
    ns = dict(i[1] for i in ET.iterparse(xml_file, events=['start-ns']))
    # users
    users = []
    for i in tree.iter('{{{wp}}}author'.format(**ns)):
        users.append(
            {
                'username': i.find('wp:author_login', ns).text,
                'email': i.find('wp:author_email', ns).text,
                'display_name': i.find('wp:author_display_name', ns).text,
            }
        )
    # articles
    articles = []
    for i in tree.iter('item'.format(**ns)):
        articles.append(
            {
                'subject': i.find('title', ns).text,
                'content': i.find('content:encoded', ns).text,
                'created_at': i.find('wp:post_date', ns).text,
                'user_id': i.find('dc:creator', ns).text,
            }
        )
    # TODO image
    print(users)
    print(articles)


if __name__ == '__main__':
    args = docopt(__doc__)

    if args['tables']:
        engine = get_db()
        from blogme.tables import metadata

        if args['create']:
            print('Creating tables...')
            metadata.create_all(engine)
        else:
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
        print(f'Created superuser with id: {res.inserted_primary_key}')
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
