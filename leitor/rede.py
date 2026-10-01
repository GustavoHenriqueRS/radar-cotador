"""Rede hospitalar de cada plano e as mudanças de rede, direto dos dados abertos da ANS.

O preço vem do material da operadora; a rede vem do registro do produto na ANS, a mesma base que a ANS
usa para fiscalizar. A rede hospitalar é um zip de 1,4 GB dividido por UF (27 CSVs, 17 GB descompactados):
com pedidos HTTP Range o leitor baixa só o trecho de cada UF, descompacta em fluxo e guarda só as linhas
dos planos acompanhados. Os pedidos de alteração de rede (exclusão, substituição, redução) vêm de outro
conjunto, um zip por ano, com o resultado da análise da ANS.

Uso: python -m leitor.rede dados/ans/rede.sqlite --planos 471312145,... [--ufs DF,SP] [--anos 2025,2026]
"""
import argparse
import csv
import gzip
import json
import re
import sqlite3
import struct
import threading
import urllib.request
import zlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

PDA = "https://dadosabertos.ans.gov.br/FTP/PDA/"
REDE = PDA + "produtos_e_prestadores_hospitalares/produtos_e_prestadores_hospitalares.zip"
ALTERACOES = PDA + "solicitacoes_alteracao_rede_hospitalar-046/"
MUNICIPIOS_IBGE = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios?view=nivelado"
AGENTE = "RadarCotador/0.1 (rede hospitalar dos planos acompanhados; dados abertos da ANS)"
BLOCO = 1 << 20
# O motivo da alteração é texto livre e pode ter ";": o filtro barato procura o código do plano em qualquer campo.
_NOVE_DIGITOS = re.compile(rb'"(\d{9})"')

ESQUEMA = """
CREATE TABLE IF NOT EXISTS rede (cd_plano TEXT, cnes TEXT, estabelecimento TEXT, classe TEXT, urgencia INTEGER,
    tipo_prestador TEXT, contrato TEXT, disponibilidade TEXT, municipio TEXT, uf TEXT, inicio TEXT, fim TEXT);
CREATE INDEX IF NOT EXISTS ix_rede_plano ON rede (cd_plano, uf);
CREATE TABLE IF NOT EXISTS alteracao (cd_plano TEXT, plano TEXT, operadora TEXT, protocolo TEXT, solicitada_em TEXT,
    tipo TEXT, motivo TEXT, excluido TEXT, excluido_cnes TEXT, excluido_municipio TEXT, excluido_uf TEXT,
    incluido TEXT, incluido_cnes TEXT, incluido_municipio TEXT, incluido_uf TEXT, resultado TEXT, alterada_em TEXT);
CREATE INDEX IF NOT EXISTS ix_alteracao_plano ON alteracao (cd_plano);
CREATE TABLE IF NOT EXISTS municipio (ibge6 TEXT PRIMARY KEY, nome TEXT, uf TEXT);
CREATE TABLE IF NOT EXISTS resumo (cd_plano TEXT, uf TEXT, hospitais INTEGER, urgencia INTEGER, PRIMARY KEY (cd_plano, uf));
CREATE TABLE IF NOT EXISTS meta (chave TEXT PRIMARY KEY, valor TEXT);
"""


@dataclass
class Membro:
    nome: str
    compactado: int
    inicio_local: int


def _pedir(url: str, inicio: int | None = None, fim: int | None = None, timeout: float = 120):
    cabecalhos = {"User-Agent": AGENTE}
    if inicio is not None:
        cabecalhos["Range"] = f"bytes={inicio}-{'' if fim is None else fim}"
    return urllib.request.urlopen(urllib.request.Request(url, headers=cabecalhos), timeout=timeout)


def membros(url: str) -> list[Membro]:
    """Os arquivos dentro de um zip remoto, lidos do diretório central no fim dele (sem baixar o resto)."""
    pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Range": "bytes=-65536"})
    with urllib.request.urlopen(pedido, timeout=120) as r:
        final, total = r.read(), int(r.headers["Content-Range"].split("/")[1])
    i = final.rfind(b"PK\x05\x06")
    if i < 0:
        raise ValueError(f"{url}: não achei o fim do zip")
    _, tamanho, deslocamento = struct.unpack("<HII", final[i + 10:i + 20])
    if deslocamento == 0xFFFFFFFF:
        raise ValueError(f"{url}: zip64 não suportado")
    diretorio = final[len(final) - (total - deslocamento):] if total - deslocamento <= len(final) else _pedir(url, deslocamento, deslocamento + tamanho - 1).read()
    saida, j = [], 0
    while diretorio[j:j + 4] == b"PK\x01\x02":
        compactado = struct.unpack("<I", diretorio[j + 20:j + 24])[0]
        nlen, xlen, clen = struct.unpack("<HHH", diretorio[j + 28:j + 34])
        saida.append(Membro(diretorio[j + 46:j + 46 + nlen].decode("utf-8", "replace"), compactado, struct.unpack("<I", diretorio[j + 42:j + 46])[0]))
        j += 46 + nlen + xlen + clen
    return saida


def linhas(url: str, membro: Membro):
    """As linhas de um CSV dentro do zip remoto, baixando e descompactando em fluxo só o trecho dele."""
    with _pedir(url, membro.inicio_local, membro.inicio_local + 29) as r:
        cabecalho_local = r.read()
    nlen, xlen = struct.unpack("<HH", cabecalho_local[26:30])
    inicio = membro.inicio_local + 30 + nlen + xlen
    descompactador, resto = zlib.decompressobj(-15), b""
    with _pedir(url, inicio, inicio + membro.compactado - 1, timeout=600) as r:
        while bloco := r.read(BLOCO):
            partes = (resto + descompactador.decompress(bloco)).split(b"\n")
            resto = partes.pop()
            yield from partes
    if resto := resto + descompactador.flush():
        yield from resto.split(b"\n")


def _campos(linha: bytes) -> list[str]:
    return next(csv.reader([linha.decode("utf-8", "replace").rstrip("\r")], delimiter=";"))


def _registros(url: str, membro: Membro, filtro):
    """Cada linha do CSV como dicionário, só as que passam no filtro barato sobre os bytes."""
    colunas = None
    for linha in linhas(url, membro):
        if colunas is None:
            colunas = _campos(linha)
            continue
        if linha.strip() and filtro(linha):
            yield dict(zip(colunas, _campos(linha)))


def _plano_da_linha(linha: bytes) -> bytes:
    """O código do plano é o 7º campo; linha quebrada por uma quebra de linha dentro de um nome não tem 7 campos."""
    campos = linha.split(b";", 7)
    return campos[6].strip(b'"') if len(campos) > 6 else b""


def _municipios(db: sqlite3.Connection):
    with _pedir(MUNICIPIOS_IBGE) as r:
        bruto = r.read()
    # A API do IBGE responde compactada mesmo sem o cliente pedir.
    dados = json.loads(gzip.decompress(bruto) if bruto[:2] == b"\x1f\x8b" else bruto)
    db.executemany("INSERT OR REPLACE INTO municipio VALUES (?, ?, ?)",
                   [(str(m["municipio-id"])[:6], m["municipio-nome"], m["UF-sigla"]) for m in dados])


def resumir(db: sqlite3.Connection):
    """Hospitais com vínculo ativo por plano e UF, calculados uma vez na montagem e não a cada cotação.

    O estabelecimento (CNES) fica num município só, então o total do plano é a soma das UFs.
    """
    db.execute("DELETE FROM resumo")
    db.execute("INSERT INTO resumo SELECT cd_plano, uf, COUNT(DISTINCT cnes), COUNT(DISTINCT CASE WHEN urgencia = 1 THEN cnes END) "
               "FROM rede WHERE fim IS NULL OR fim = '' GROUP BY cd_plano, uf")


def construir(destino: Path, planos: set[str], ufs: set[str] | None = None, anos: list[int] | None = None, avisar=print) -> dict:
    """Monta (ou refaz) o SQLite com a rede e as alterações de rede dos planos pedidos."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_suffix(".tmp")
    temporario.unlink(missing_ok=True)
    db = sqlite3.connect(temporario)
    db.executescript(ESQUEMA)
    _municipios(db)
    nomes = dict(db.execute("SELECT ibge6, nome FROM municipio"))
    alvo = {p.encode() for p in planos}
    contagem = {"rede": 0, "alteracoes": 0}
    for membro in membros(REDE):
        uf = re.search(r"_([A-Z]{2})\.csv$", membro.nome)
        if not uf or (ufs and uf.group(1) not in ufs):
            continue
        avisar(f"rede {uf.group(1)}: {membro.compactado / 2**20:.0f} MB")
        # O código do plano é o 7º campo: o filtro sobre os bytes vem antes do parser de CSV (17 GB de texto).
        lote = [(r["CD_PLANO"], r["CD_CNES"], r["NM_ESTABELECIMENTO_SAUDE"], r["DE_CLAS_ESTB_SAUDE"], int(r["LG_URGENCIA_EMERGENCIA"] == "1"),
                 r["DE_TIPO_PRESTADOR"], r["DE_TIPO_CONTRATO"], r["DE_DISPONIBILIDADE"],
                 r["NM_MUNICIPIO"] or nomes.get(r["CD_MUNICIPIO"], r["CD_MUNICIPIO"]), r["SG_UF"], r["DT_VINCULO_INICIO"], r["DT_VINCULO_FIM"])
                for r in _registros(REDE, membro, lambda linha: _plano_da_linha(linha) in alvo)]
        db.executemany("INSERT INTO rede VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", lote)
        contagem["rede"] += len(lote)
    with _pedir(ALTERACOES) as r:
        disponiveis = sorted({int(a) for a in re.findall(r"rede_hospitalar-(\d{4})\.zip", r.read().decode("utf-8", "replace"))})
    for ano in anos or disponiveis[-2:]:
        url = f"{ALTERACOES}pda-046-solicitacoes_alteracao_rede_hospitalar-{ano}.zip"
        for membro in membros(url):
            avisar(f"alterações de rede {ano}: {membro.compactado / 2**20:.0f} MB")
            lote = [(r["CD_PLANO"], r["NM_PLANO"], r["RAZAO_SOCIAL"], r["CD_PROTOCOLO_SOLICITACAO"], r["DT_SOLICITACAO"], r["TP_SOLICITACAO"],
                     r["MOTIVO"], r["NM_PRESTADOR_EXCLUIDO"], r["CNES_PRESTADOR_EXCLUIDO"], r["NM_MUNICIPIO_PRESTADOR_EXCLUIDO"], r["UF_PRESTADOR_EXCLUIDO"],
                     r["NM_PRESTADOR_INCLUIDO"], r["CNES_PRESTADOR_INCLUIDO"], r["NM_MUNICIPIO_PRESTADOR_INCLUIDO"], r["UF_PRESTADOR_INCLUIDO"],
                     r["RESULTADO"], r["DT_ALTERACAO"])
                    for r in _registros(url, membro, lambda linha: any(m in alvo for m in _NOVE_DIGITOS.findall(linha)))
                    if r["CD_PLANO"] in planos]
            db.executemany("INSERT INTO alteracao VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", lote)
            contagem["alteracoes"] += len(lote)
    resumir(db)
    db.executemany("INSERT OR REPLACE INTO meta VALUES (?, ?)", [
        ("atualizado_em", datetime.now().isoformat(timespec="seconds")), ("planos", str(len(planos))),
        ("ufs", ",".join(sorted(ufs)) if ufs else "todas"), ("fonte", REDE)])
    db.commit()
    db.close()
    temporario.replace(destino)
    return contagem


class IndiceRede:
    """Consulta somente leitura; uma conexão por thread, como o índice da ANS."""

    def __init__(self, caminho: Path):
        self.caminho = Path(caminho)
        self._local = threading.local()

    @property
    def db(self) -> sqlite3.Connection:
        # A atualização troca o arquivo inteiro: conexão aberta no arquivo anterior é refeita.
        versao = self.caminho.stat().st_mtime_ns
        db = getattr(self._local, "db", None)
        if db is None or getattr(self._local, "versao", None) != versao:
            db = sqlite3.connect(f"file:{self.caminho}?mode=ro", uri=True)
            db.row_factory = sqlite3.Row
            self._local.db, self._local.versao = db, versao
        return db

    def atualizado_em(self) -> str | None:
        linha = self.db.execute("SELECT valor FROM meta WHERE chave = 'atualizado_em'").fetchone()
        return linha[0] if linha else None

    def hospitais(self, cd_plano: str, uf: str | None = None) -> list[dict]:
        """Um registro por hospital (o mesmo CNES aparece uma vez por vínculo), com pronto-socorro primeiro."""
        sql = ("SELECT cnes, estabelecimento, classe, MAX(urgencia) AS urgencia, municipio, uf, contrato, disponibilidade "
               "FROM rede WHERE cd_plano = ? AND (fim IS NULL OR fim = '')" + (" AND uf = ?" if uf else "") +
               " GROUP BY cnes ORDER BY urgencia DESC, uf, municipio, estabelecimento")
        return [dict(r) for r in self.db.execute(sql, (cd_plano, uf) if uf else (cd_plano,))]

    def resumo(self, cd_plano: str) -> dict:
        linhas = self.db.execute("SELECT uf, hospitais, urgencia FROM resumo WHERE cd_plano = ? ORDER BY hospitais DESC, uf", (cd_plano,)).fetchall()
        return {"hospitais": sum(r["hospitais"] for r in linhas),
                "por_uf": {r["uf"]: {"hospitais": r["hospitais"], "urgencia": r["urgencia"]} for r in linhas}}

    def alteracoes(self, cd_plano: str) -> list[dict]:
        return [dict(r) for r in self.db.execute(
            "SELECT * FROM alteracao WHERE cd_plano = ? ORDER BY solicitada_em DESC, protocolo", (cd_plano,))]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Rede hospitalar e alterações de rede dos planos, dos dados abertos da ANS.")
    ap.add_argument("destino", type=Path)
    ap.add_argument("--planos", required=True, help="códigos de plano (registro ANS do produto, 9 dígitos), separados por vírgula")
    ap.add_argument("--ufs", help="só estas UFs (ex.: DF,SP); padrão: todas")
    ap.add_argument("--anos", help="anos de alterações de rede; padrão: os dois últimos publicados")
    args = ap.parse_args()
    print(construir(args.destino, set(args.planos.split(",")), set(args.ufs.upper().split(",")) if args.ufs else None,
                    [int(a) for a in args.anos.split(",")] if args.anos else None))
