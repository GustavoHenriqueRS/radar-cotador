#!/bin/sh
set -e
cd /app/backend
python manage.py migrate --noinput
# Primeira subida: baixa os dados abertos da ANS, monta o índice e carrega o acervo de demonstração.
if [ "${CARREGAR_DEMO:-1}" = "1" ] && ! python manage.py shell -c "import sys; from radar.models import Documento; sys.exit(0 if Documento.objects.exists() else 1)" >/dev/null 2>&1; then
  python manage.py carregar_demo
fi
exec gunicorn config.wsgi --bind 0.0.0.0:8000 --workers 2 --threads 4 --timeout 600
