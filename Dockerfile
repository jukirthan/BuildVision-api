FROM python:3.12.8-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . ./

CMD ["sh", "-c", "exec gunicorn run:app --bind 0.0.0.0:${PORT:?PORT must be set by Railway} --workers 2 --timeout 120"]
