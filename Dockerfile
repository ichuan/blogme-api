FROM python:3.7-slim
EXPOSE 8000
WORKDIR /app

RUN apt update && apt install -y --no-install-recommends build-essential fswatch imagemagick

COPY . /app/
RUN pip install --no-cache-dir pipenv
RUN pipenv install --deploy --system --ignore-pipfile

# cleanup
RUN apt remove -y build-essential && apt autoremove -y
RUN rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["supervisord", "-nc", "/app/supervisord.conf"]
