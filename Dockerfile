# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /app

# Dependências de sistema mínimas (se precisar compilar libs)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Instala dependências do backend
COPY server/requirements.txt /app/server/requirements.txt
RUN pip install --no-cache-dir -r /app/server/requirements.txt

# Copia o backend
COPY server /app/server

EXPOSE 8000

# Sobe o FastAPI com Uvicorn
CMD ["sh", "-c", "uvicorn server.main:app --host 0.0.0.0 --port ${PORT}"]