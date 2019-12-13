# blogme-api


# Setup

```sh
# create database tables
python tables.py create
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
