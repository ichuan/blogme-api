# blogme-api


# Setup

```sh
# create database
mysql -uroot -e 'CREATE DATABASE blogme CHARACTER SET utf8;'

# create database tables
python blogme/cmd.py create tables

# create superuser (username: root, password: R00t!)
python blogme/cmd.py create superuser

# install self
pipenv install -e .
```


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
