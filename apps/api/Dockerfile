FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Install dependencies first for better layer caching.
COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Copy the API source (includes alembic.ini + migrations + app package).
COPY apps/api/ /app/

EXPOSE 8000

