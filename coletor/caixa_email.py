"""Caixa de e-mail que recebe os materiais (o caso de quem não publica em página aberta ou bloqueia robôs).

Cada PDF anexado, solto ou dentro de um .zip, num e-mail de remetente autorizado vira um candidato.
A caixa é aberta só para leitura (EXAMINE): nada é marcado como lido, movido ou apagado. A senha não fica
no banco: a configuração diz o nome da variável de ambiente que a guarda.
"""
import email
import imaplib
import io
import os
import re
import zipfile
from datetime import date, datetime
from email import policy
from email.utils import parseaddr, parsedate_to_datetime
from urllib.parse import quote

from .base import PADRAO_DATA, Candidato, Coletor, chave_da_serie, data_no_nome
from .http import LIMITE_BYTES

CABECALHOS = "(UID BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE AUTHENTICATION-RESULTS)])"
MESES_IMAP = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _autenticado(mensagem, dominio: str, autenticado_por: str = "") -> bool:
    """O servidor de e-mail confirmou que a mensagem é mesmo do domínio (DMARC, ou DKIM assinado por ele).

    O campo From se falsifica com facilidade; a assinatura DKIM e o alinhamento DMARC, não. Com
    `autenticado_por`, só vale o resultado registrado pelo próprio servidor da caixa (RFC 8601).
    """
    dominio = re.escape(dominio.lower())
    for valor in mensagem.get_all("Authentication-Results", []):
        valor = " ".join(str(valor).lower().split())
        if autenticado_por and not valor.startswith(autenticado_por.lower()):
            continue
        for resultado in valor.split(";"):
            if re.search(rf"\bdmarc=pass\b.*\bheader\.from=(?:[\w-]+\.)*{dominio}\b", resultado):
                return True
            if re.search(rf"\bdkim=pass\b.*\bheader\.[di]=@?(?:[\w-]+\.)*{dominio}\b", resultado):
                return True
    return False


def _literal(dados) -> bytes | None:
    """O conteúdo devolvido pelo FETCH; None se a mensagem sumiu entre a busca e a leitura."""
    return next((p[1] for p in dados or [] if isinstance(p, tuple)), None)


def _remetente_autorizado(endereco: str, remetentes: list[str]) -> bool:
    endereco = endereco.lower()
    dominio = endereco.rpartition("@")[2]
    for r in (r.lower().strip() for r in remetentes):
        if r.startswith("@") and (dominio == r[1:] or dominio.endswith("." + r[1:])):
            return True
        if r == endereco:
            return True
    return False


def _pdfs(mensagem) -> list[tuple[str, bytes]]:
    """(nome, conteúdo) de cada PDF anexado, inclusive dentro de .zip e de e-mail encaminhado."""
    encontrados = []
    for parte in mensagem.walk():
        if parte.is_multipart():
            continue
        nome = parte.get_filename() or ""
        tipo = parte.get_content_type()
        if not (nome.lower().endswith((".pdf", ".zip")) or tipo in ("application/pdf", "application/zip")):
            continue
        conteudo = parte.get_payload(decode=True) or b""
        if conteudo.startswith(b"%PDF"):
            encontrados.append((nome or "anexo.pdf", conteudo))
        elif conteudo.startswith(b"PK"):
            with zipfile.ZipFile(io.BytesIO(conteudo)) as z:
                for info in z.infolist():
                    if info.filename.lower().endswith(".pdf") and info.file_size <= LIMITE_BYTES:
                        dentro = z.read(info)
                        if dentro.startswith(b"%PDF"):
                            encontrados.append((info.filename.rsplit("/", 1)[-1], dentro))
    return encontrados


class CaixaEmail(Coletor):
    """Configuração:

    - servidor, porta (993), ssl (sim), usuario, senha_env (variável de ambiente com a senha), pasta (INBOX);
      servidor_env: variável de ambiente que, se definida, troca o servidor (o mesmo arquivo de fonte serve
      para a máquina local e para o Docker);
    - remetentes: endereços ou domínios autorizados ("@unimed.coop.br"); o resto é ignorado;
    - exigir_autenticacao (sim): só aceita o remetente confirmado por DMARC ou DKIM; autenticado_por: o
      identificador do servidor da caixa no cabeçalho Authentication-Results (ex.: mx.google.com);
    - assunto: expressão que o assunto precisa conter (opcional);
    - desde: AAAA-MM-DD, o e-mail mais antigo a considerar na primeira coleta;
    - max_mensagens: quantas mensagens novas ler por coleta (50).
    """

    tipo = "caixa_email"
    rotulo = "Caixa de e-mail"
    obrigatorios = ("servidor", "usuario", "senha_env", "remetentes")
    imutavel = True

    def descobrir(self, config: dict, http, estado: dict) -> list[Candidato]:
        senha = os.environ.get(config.get("senha_env", ""), "")
        if not senha:
            raise ValueError(f"a senha da caixa fica na variável de ambiente indicada em senha_env ({config.get('senha_env') or 'não configurada'})")
        servidor = os.environ.get(config.get("servidor_env", ""), "") or config["servidor"]
        usuario, pasta = config["usuario"], config.get("pasta", "INBOX")
        classe = imaplib.IMAP4_SSL if config.get("ssl", True) else imaplib.IMAP4
        caixa = classe(servidor, int(config.get("porta", 993 if config.get("ssl", True) else 143)), timeout=60)
        try:
            caixa.login(usuario, senha)
            situacao, _ = caixa.select(f'"{pasta}"', readonly=True)
            if situacao != "OK":
                raise ValueError(f"a pasta {pasta} não existe na caixa {usuario}")
            validade = (caixa.response("UIDVALIDITY")[1] or [b""])[0]
            validade = validade.decode() if isinstance(validade, bytes) else str(validade or "")
            # Outro UIDVALIDITY quer dizer que os números das mensagens foram refeitos: recomeça do zero.
            ultimo = int(estado.get("ultimo_uid", 0)) if estado.get("uidvalidade") == validade else 0
            criterios = ["UID", f"{ultimo + 1}:*"]
            if not ultimo and config.get("desde"):
                d = date.fromisoformat(config["desde"])
                criterios += ["SINCE", f"{d.day:02d}-{MESES_IMAP[d.month - 1]}-{d.year}"]
            _, dados = caixa.uid("SEARCH", *criterios)
            # "N:*" devolve ao menos a última mensagem, mesmo que já lida.
            uids = sorted(u for u in (int(x) for x in (dados[0] or b"").split()) if u > ultimo)
            uids = uids[: int(config.get("max_mensagens", 50))]
            candidatos = []
            for uid in uids:
                candidatos += self._da_mensagem(caixa, uid, config, f"imap://{quote(usuario)}@{servidor}/{quote(pasta)};UIDVALIDITY={validade}/;UID={uid}")
            if uids:
                estado.update(uidvalidade=validade, ultimo_uid=uids[-1])
            return candidatos
        finally:
            try:
                caixa.logout()
            except (imaplib.IMAP4.error, OSError):
                pass

    def _da_mensagem(self, caixa, uid: int, config: dict, endereco: str) -> list[Candidato]:
        _, dados = caixa.uid("FETCH", str(uid), CABECALHOS)
        if (bruto := _literal(dados)) is None:
            return []
        cabecalho = email.message_from_bytes(bruto, policy=policy.default)
        remetente = parseaddr(str(cabecalho.get("From", "")))[1].lower()
        assunto = str(cabecalho.get("Subject", ""))
        if not _remetente_autorizado(remetente, config.get("remetentes", [])):
            return []
        if config.get("exigir_autenticacao", True) and not _autenticado(cabecalho, remetente.rpartition("@")[2], config.get("autenticado_por", "")):
            return []
        if config.get("assunto") and not re.search(config["assunto"], assunto, re.I):
            return []
        _, dados = caixa.uid("FETCH", str(uid), "(UID BODY.PEEK[])")
        if (bruto := _literal(dados)) is None:
            return []
        mensagem = email.message_from_bytes(bruto, policy=policy.default)
        try:
            recebido = parsedate_to_datetime(str(mensagem.get("Date"))).date()
        except (TypeError, ValueError):
            recebido = datetime.now().date()
        dominio = remetente.rpartition("@")[2]
        candidatos = []
        for indice, (nome, conteudo) in enumerate(_pdfs(mensagem), start=1):
            candidatos.append(Candidato(
                url=f"{endereco}/;PARTE={indice}",
                titulo=assunto[:300],
                nome_arquivo=nome,
                conteudo=conteudo,
                data_versao=data_no_nome(f"https://{dominio}/{nome}", config.get("data_no_nome", PADRAO_DATA)) or recebido,
                chave_serie=chave_da_serie(f"https://{dominio}/{nome}", config.get("data_no_nome", PADRAO_DATA)),
                observacoes=[f"e-mail de {remetente} recebido em {recebido:%d/%m/%Y}: {assunto}"[:300]],
            ))
        return candidatos
