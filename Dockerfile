FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 ca-certificates build-essential gcc g++ \
    && rm -rf /var/lib/apt/lists/*

ENV CC=/usr/bin/gcc
ENV CXX=/usr/bin/g++

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install torch==2.14.0+cu130 torchaudio==2.11.0+cu130 --index-url https://download.pytorch.org/whl/cu130 \
    && python -m pip install -r /app/requirements.txt

COPY app /app/app

RUN mkdir -p /data/voices /data/media /data/hf-cache

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8787"]
