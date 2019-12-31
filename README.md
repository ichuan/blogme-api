# blogme-api


# Setup

Deps:

- imagemagick (convert)


```sh
# create database
mysql -uroot -e 'CREATE DATABASE blogme CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'

# create database tables
python blogme/bin/cmd.py create tables

# create superuser (username: root, password: R00t!)
python blogme/bin/cmd.py create superuser

# install self
pipenv install -e .
```

Docs at http://127.0.0.1:8000/docs


# Develop

```sh
pipenv install --dev
uvicorn blogme.main:app --reload
```

# Deploy

```sh
pipenv sync
uvicorn blogme.main:app
```


# Import blog data from wordpress

1. Export wordpress as `WordPress.XXXX-XX-XX.xml`
2. `python blogme/bin/cmd.py import wordpress WordPress.XXXX-XX-XX.xml`


# Docker
## ENV
- `DB_USER`: default: root
- `DB_PASS`: default: "" (empty)
- `DB_HOST`: default: localhost
- `DB_NAME`: default: blogme
- `SECRET_KEY`: default: (generated per container)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: default: 1440 (24 hours)
- `CORS_ORIGINS`: space-seprated, default: "http://localhost:3000"
