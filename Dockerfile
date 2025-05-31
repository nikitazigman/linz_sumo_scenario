FROM python:3.12-slim AS sumo

ENV SUMO_HOME=/usr/share/sumo

ARG APP_PATH=/opt/app

ENV SUMO_HOME=/usr/share/sumo \
  PYTHONUNBUFFERED=1 \
  # Prevents python creating .pyc files
  PYTHONDONTWRITEBYTECODE=1 \
  # Pip
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  # Poetry
  POETRY_VERSION=1.6.1 \
  # Make poetry install to this location
  POETRY_HOME="/usr/local" \
  # Make poetry not create a virtual environment
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR="/var/cache/pypoetry" \
  # Do not ask any interactive question
  POETRY_NO_INTERACTION=1

# install sumo 
RUN apt-get update && apt-get install --no-install-recommends -y curl build-essential sumo sumo-tools sumo-doc
# install poetry 
RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR ${APP_PATH}

# Copy app code to WORKDIR
COPY  ./h2mob ${APP_PATH}
RUN poetry install
