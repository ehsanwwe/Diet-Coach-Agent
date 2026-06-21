FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:$PATH" \
    BACKEND_INTERNAL_PORT=8000

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && python -m venv /opt/venv

COPY requirements.txt ./requirements.txt
COPY pyproject.toml* ./

ARG PIP_INDEX_URL=https://package-mirror.liara.ir/repository/pypi/simple
ARG PIP_TRUSTED_HOST=

ENV PIP_INDEX_URL=${PIP_INDEX_URL} \
    PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST}

RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

COPY alembic.ini ./alembic.ini
COPY alembic ./alembic
COPY app ./app

RUN mkdir -p /app/persistent /app/persistent/storage /app/persistent/uploads /app/persistent/audio

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import os,socket; p=int(os.getenv('BACKEND_INTERNAL_PORT','8000')); s=socket.create_connection(('127.0.0.1',p),3); s.close()"

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${BACKEND_INTERNAL_PORT:-8000}"]


