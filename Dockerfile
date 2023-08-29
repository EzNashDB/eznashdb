ARG PYTHON_VERSION=3.10-slim-buster
ARG NODE_VERSION=18.16.0

FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_VERSION=1.2.2

RUN pip install "poetry==$POETRY_VERSION"

RUN apt-get update && apt-get -y install nodejs=$NODE_VERSION

RUN mkdir -p /code

WORKDIR /code
COPY poetry.lock pyproject.toml /code/

RUN poetry config virtualenvs.create false \
  && poetry install $(test "$DEBUG" != True && echo "--only main") --no-interaction --no-ansi

RUN npm install

COPY . /code/

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", ":8000", "--workers", "2", "app.wsgi"]
