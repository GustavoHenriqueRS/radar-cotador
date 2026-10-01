#!/bin/sh
# Sobe o protótipo completo em qualquer máquina com Docker, por um túnel da Cloudflare, com senha (padrão) ou aberto.
# Nenhuma porta é aberta no servidor, e o endereço público (https://...trycloudflare.com) aparece no fim.
# O endereço muda se o túnel reiniciar. A senha não é gravada em lugar nenhum: o Caddy recebe só o hash.
# Uso: ACESSO_SENHA=... ./deploy/subir-com-tunel.sh   ou   ACESSO_HASH='<hash do caddy>' ./deploy/subir-com-tunel.sh
# Sem senha, para um endereço que só vai para quem vai usar: ACESSO_ABERTO=1 ./deploy/subir-com-tunel.sh
set -e
cd "$(dirname "$0")/.."

export ACESSO_USUARIO="${ACESSO_USUARIO:-avaliador}"
if [ "$ACESSO_ABERTO" = "1" ]; then
  export ACESSO_CADDYFILE=Caddyfile.tunel-aberto
elif [ -z "$ACESSO_HASH" ]; then
  if [ -z "$ACESSO_SENHA" ]; then
    echo "defina ACESSO_SENHA ou ACESSO_HASH, ou use ACESSO_ABERTO=1" >&2
    exit 2
  fi
  ACESSO_HASH=$(docker run --rm caddy:2.10-alpine caddy hash-password --plaintext "$ACESSO_SENHA")
fi
export ACESSO_HASH

compose="docker compose -p radar-cotador -f docker-compose.yml -f deploy/compose.tunel.yml"
$compose up -d --build

endereco=""
for _ in $(seq 1 60); do
  endereco=$($compose logs tunel 2>/dev/null | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' | tail -n 1)
  [ -n "$endereco" ] && break
  sleep 5
done
echo "protótipo: ${endereco:-ainda sem endereço; veja com: $compose logs tunel}"
if [ "$ACESSO_ABERTO" = "1" ]; then echo "acesso: aberto, sem senha"; else echo "usuário: $ACESSO_USUARIO"; fi
echo "Na primeira subida o app ainda baixa os dados da ANS e carrega o acervo; até terminar, o endereço responde 502."
