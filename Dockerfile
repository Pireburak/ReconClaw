FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 PORT=8000 RECONCLAW_DB=/app/data/reconclaw.db

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN useradd --create-home --uid 1000 reconclaw && mkdir -p /app/data && chown -R reconclaw /app/data
USER reconclaw

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"
# Caddy arkasında çalıştığı için X-Forwarded-* başlıklarına güvenilir
CMD ["sh", "-c", "uvicorn main:app --host $HOST --port $PORT --proxy-headers --forwarded-allow-ips='*'"]
