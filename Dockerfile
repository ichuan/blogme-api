FROM python:3.7-slim
EXPOSE 8000
WORKDIR /app
ENV PIPENV_VENV_IN_PROJECT=1

RUN apt update && apt install -y build-essential fswatch imagemagick

COPY . /app/
RUN pip install --no-cache-dir pipenv
RUN pipenv install -e .
RUN pipenv sync

# cleanup
RUN rm -rf /var/lib/apt/lists/*

ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["supervisord", "-nc", "/app/supervisord.conf"]
