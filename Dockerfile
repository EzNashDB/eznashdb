ARG PYTHON_VERSION=3.10-slim-buster

FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_VERSION=1.2.2
ENV NODE_VERSION=18.16.0

RUN pip install "poetry==$POETRY_VERSION"

# Install Node.js and npm using apt
RUN apt-get update && apt-get install -y \
    curl \
 && curl -sL https://deb.nodesource.com/setup_18.x | bash - \
 && apt-get install -y nodejs

RUN mkdir -p /code

WORKDIR /code
COPY poetry.lock pyproject.toml /code/

RUN poetry config virtualenvs.create false \
  && poetry install $(test "$DEBUG" != True && echo "--only main") --no-interaction --no-ansi

COPY . /code/

RUN npm install

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", ":8000", "--workers", "2", "app.wsgi"]
