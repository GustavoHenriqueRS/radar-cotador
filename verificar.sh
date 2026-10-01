#!/bin/sh
# O que precisa passar antes de qualquer entrega: fontes válidas, testes do leitor e do coletor, testes do Django e o build do frontend.
set -e
cd "$(dirname "$0")"
echo "== fontes"
PYTHONPATH=. .venv/bin/python -m coletor.fontes
echo "== leitor e coletor"
.venv/bin/python -m pytest -q
echo "== Django"
(cd backend && ../.venv/bin/python manage.py check && ../.venv/bin/python manage.py makemigrations --check --dry-run && ../.venv/bin/python manage.py test radar)
echo "== frontend"
(cd frontend && npx tsc --noEmit && npm run build)
echo "tudo certo"
