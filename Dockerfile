# Minimal image for running reading_reels Telegram bot anywhere (Railway / Render / Fly.io).
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    espeak-ng ca-certificates ffmpeg \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Force cache invalidation — increment on each deploy
RUN echo "deploy-v5" > /deploy-marker

COPY . .

# Run the Telegram bot (interactive, polling mode)
CMD ["python", "-m", "app.main", "bot"]
