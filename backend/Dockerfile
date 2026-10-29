FROM python:3.12-slim AS build

WORKDIR /build
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /install /usr/local
WORKDIR /app
COPY backend /app/backend
COPY runner /app/runner
ENV PYTHONPATH=/app/backend:/app
ENV PYTHONUNBUFFERED=1
WORKDIR /app/backend
EXPOSE 8000
CMD ["python", "entrypoint.py"]
