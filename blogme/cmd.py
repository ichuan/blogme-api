#!/usr/bin/env python
# coding: utf-8
# yc@2019/12/12

'''
Usage:
    cmd.py create tables
    cmd.py drop tables
    cmd.py create superuser [--username=NAME] [--password=PASS]
    cmd.py test

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


if __name__ == '__main__':
    args = docopt(__doc__)

    if args['tables']:
        from blogme.tables import metadata
        engine = get_db()
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
    elif args['test']:
        pass
