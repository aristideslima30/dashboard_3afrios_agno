# Backend 3A Frios - Dockerfile para deploy na Railway
FROM python:3.11-slim

# Evita .pyc e logs bufferizados
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copia requirements e instala dependências do backend
COPY server/requirements.txt /app/server/requirements.txt
RUN pip install --no-cache-dir -r /app/server/requirements.txt

# Copia o código do backend
COPY server/ /app/server/

# Porta padrão; Railway injeta PORT automaticamente
ENV PORT=8000

# Inicia o uvicorn usando a variável PORT do ambiente
CMD ["sh", "-c", "python -m uvicorn server.main:app --host 0.0.0.0 --port ${PORT}"]