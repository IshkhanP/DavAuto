FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend requirements first for better layer caching
COPY backend/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# Copy the rest of the backend source
COPY backend/ .

EXPOSE 8000

# Default command (overridden by docker-compose for one-shot migrations)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]