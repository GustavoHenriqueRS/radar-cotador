#!/bin/sh
# Gera a versão estática do protótipo, a que roda no GitHub Pages sem servidor.
# Precisa do protótipo no ar (docker compose up) com o acervo de demonstração carregado.
# Uso: ./scripts/gerar_demo_estatica.sh [pasta de saída]
set -e
cd "$(dirname "$0")/.."
SAIDA=${1:-dados/demo-estatica}

docker compose exec -T app sh -c "rm -rf /tmp/demo && python backend/manage.py exportar_demo /tmp/demo"
rm -rf "$SAIDA"
(cd frontend && VITE_DEMO_ESTATICA=1 VITE_DEMO_DATA="$(date +%d/%m/%Y)" npx vite build --base=/radar-cotador/ --outDir "$(cd .. && pwd)/$SAIDA" --emptyOutDir)
docker compose cp app:/tmp/demo "$SAIDA/demo"
touch "$SAIDA/.nojekyll"
mkdir -p "$SAIDA/pdf" && cp docs/pdf/*.pdf "$SAIDA/pdf/"
# Os vídeos e as capas vão junto quando já estão em dados/video.
if [ -f dados/video/radar-cotador-demo.mp4 ]; then
  mkdir -p "$SAIDA/video" && cp dados/video/*.mp4 dados/video/*.jpg "$SAIDA/video/"
fi
echo "versão estática em $SAIDA"
