ARG PYTHON_VERSION=3.10-slim-bullseye

FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_VERSION=1.6.1
ENV NODE_VERSION=22.13.1
ENV NODE_OPTIONS="--max-old-space-size=128"


RUN pip install "poetry==$POETRY_VERSION"

# Install system dependencies and PostgreSQL 15 client
RUN apt-get update && \
    apt-get install -y ca-certificates curl gnupg unzip && \
    curl https://rclone.org/install.sh | bash && \
    # Add PostgreSQL apt repository for version 15
    curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /usr/share/keyrings/postgresql-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/postgresql-keyring.gpg] http://apt.postgresql.org/pub/repos/apt bullseye-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    apt-get update && \
    apt-get remove -y postgresql-client-* || true && \
    apt-get install -y postgresql-client-15 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Node.js and npm, per https://stackoverflow.com/a/77021599
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
     | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    NODE_MAJOR=18 && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" \
     > /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install nodejs -y

RUN mkdir -p /code

WORKDIR /code
COPY poetry.lock pyproject.toml /code/

RUN poetry config virtualenvs.create false \
  && poetry install $(test "$DEBUG" != True && echo "--only main") --no-interaction --no-ansi

COPY . /code/

RUN npm install

RUN npm run build

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", ":8000", "--workers", "1", "--threads", "3", "app.wsgi"]
