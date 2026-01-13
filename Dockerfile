FROM python:3.12-slim

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala deps Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código
COPY src/ ./src/
COPY prd.md ./

# Cria diretório de dados
RUN mkdir -p /data

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('/data/mariabico.db') else 1)"

# Roda bot
CMD ["python", "-u", "src/main.py"]
