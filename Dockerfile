FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN cd connection_utils/db && sqlite3 db.sqlite3 < migrations.sql

RUN printf '%s\n' '{"APP_HOST":"0.0.0.0","APP_PORT":8000,"ENV":"prod","REDIS_HOST":"127.0.0.1","REDIS_PORT":6379}' > env.json

EXPOSE 8000

CMD ["python", "main.py"]