# Not build-tested in the environment this was written in (no Docker
# daemon available there) — reviewed by hand against requirements.txt and
# the app's actual startup path. Verify with `docker build .` before relying
# on it.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Uploaded images persist here — mount a volume in docker-compose/production
# so they survive container restarts (see docker-compose.yml).
RUN mkdir -p uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
