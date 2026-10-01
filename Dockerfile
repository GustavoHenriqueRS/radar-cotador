# 1) Build do React
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
# A página de apresentação usa o mesmo diagrama da documentação.
COPY docs/img/ /app/docs/img/
RUN npm run build

# 2) Django + leitor
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    DADOS_ANS=/dados/ans MEDIA_ROOT=/dados/media DJANGO_DEBUG=0 DJANGO_ALLOWED_HOSTS=*
# O OpenCV usado pelo OCR precisa destas bibliotecas.
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Baixa os modelos do OCR no build, para a demonstração não depender de internet.
RUN python -c "from rapidocr import RapidOCR; RapidOCR()"
COPY leitor/ leitor/
COPY coletor/ coletor/
COPY fontes/ fontes/
COPY backend/ backend/
COPY amostras/ amostras/
COPY docs/ docs/
COPY --from=frontend /app/frontend/dist frontend/dist
RUN cd backend && python manage.py collectstatic --noinput >/dev/null
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
