FROM python:3.12-slim

# Instalar dependencias do sistema para Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg2 \
    libnss3 \
    libatk-bridge2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libxshmfence1 \
    fonts-liberation \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar browser do Playwright
RUN playwright install chromium
RUN playwright install-deps chromium

# Copiar codigo da aplicacao
COPY config.py .
COPY degustone_scraper.py .
COPY consolidate_data.py .
COPY api_server.py .

# Criar diretorio de saida
RUN mkdir -p /app/relatorios

# Expor porta padrao do n8n/Easypanel E a porta da aplicacao
EXPOSE 3000
EXPOSE 5679

# Health check para garantir que a API esta respondendo
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5679/health || exit 1

# Rodar API server
CMD ["python", "-u", "api_server.py"]
