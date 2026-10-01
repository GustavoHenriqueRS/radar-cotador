"""Índice local dos dados abertos da ANS (catálogo de planos, operadoras e nota técnica de preço).

Os arquivos oficiais são grandes (o VCM tem 339 MB em 23 CSVs); o índice guarda em
SQLite só o que o leitor consulta: o plano pelo registro, a operadora e a nota
técnica mais recente de cada plano ativo ou suspenso.
"""
import csv
import io
import sqlite3
import threading
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .faixas import FAIXAS_ANS

URL_BASE = "https://dadosabertos.ans.gov.br/FTP/PDA"
ARQUIVOS = {
    "Relatorio_cadop.csv": f"{URL_BASE}/operadoras_de_plano_de_saude_ativas/Relatorio_cadop.csv",
    "Relatorio_cadop_canceladas.csv": f"{URL_BASE}/operadoras_de_plano_de_saude_canceladas/Relatorio_cadop_canceladas.csv",
    "pda-008-caracteristicas_produtos.csv": f"{URL_BASE}/caracteristicas_produtos_saude_suplementar-008/pda-008-caracteristicas_produtos_saude_suplementar.csv",
    "nota_tecnica_vcm_faixa_etaria.zip": f"{URL_BASE}/nota_tecnica_ntrp_vcm_faixa_etaria/nota_tecnica_vcm_faixa_etaria.zip",
}


@dataclass
class PlanoANS:
    id_plano: str
    cd_plano: str
    nome: str
    registro_operadora: str
    operadora: str
    contratacao: str
    segmentacao: str
    obstetricia: str
    abrangencia: str
    fator_moderador: str
    acomodacao: str
    livre_escolha: str
    situacao: str
    dt_situacao: str


@dataclass
class NotaTecnica:
    cd_nota: str
    dt_ntrp: str
    abrangencia: str  # UNICA | REGIONALIZADA
    vcm: list[float | None]
    minimo: list[float | None]
    maximo: list[float | None]


def _operadora(codigo: str) -> str:
    return str(codigo).strip().zfill(6)


def _data_iso(ddmmaaaa: str) -> str:
    d, m, a = ddmmaaaa[:10].split("/")
    return f"{a}-{m}-{d}"


def construir_indice(pasta_dados: Path, destino: Path) -> Path:
    destino.unlink(missing_ok=True)
    db = sqlite3.connect(destino)
    db.executescript(
        """
        CREATE TABLE operadora (registro TEXT PRIMARY KEY, cnpj TEXT, razao_social TEXT, nome_fantasia TEXT,
                                modalidade TEXT, uf TEXT, ativa INTEGER, data_cancelamento TEXT, motivo_cancelamento TEXT);
        CREATE TABLE plano (id_plano TEXT PRIMARY KEY, cd_plano TEXT, nome TEXT, registro_operadora TEXT, operadora TEXT,
                            vigencia TEXT, contratacao TEXT, segmentacao TEXT, obstetricia TEXT, abrangencia TEXT,
                            fator_moderador TEXT, acomodacao TEXT, livre_escolha TEXT, situacao TEXT, dt_situacao TEXT);
        CREATE INDEX plano_cd ON plano (cd_plano);
        CREATE TABLE nota (id_plano TEXT, cd_nota TEXT, dt_ntrp TEXT, abrangencia TEXT, faixa INTEGER,
                           vcm REAL, minimo REAL, maximo REAL);
        CREATE INDEX nota_plano ON nota (id_plano);
        CREATE TABLE meta (chave TEXT PRIMARY KEY, valor TEXT);
        """
    )
    for nome, ativa in (("Relatorio_cadop.csv", 1), ("Relatorio_cadop_canceladas.csv", 0)):
        with open(pasta_dados / nome, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f, delimiter=";"):
                db.execute(
                    "INSERT OR REPLACE INTO operadora VALUES (?,?,?,?,?,?,?,?,?)",
                    (_operadora(r["REGISTRO_OPERADORA"]), r["CNPJ"], r["RAZAO_SOCIAL"].strip(), r["NOME_FANTASIA"].strip(),
                     r["MODALIDADE"], r["UF"], ativa, r.get("DATA_DESCREDENCIAMENTO"), r.get("MOTIVO_DO_DESCREDENCIAMENTO")),
                )

    ativos: set[str] = set()
    with open(pasta_dados / "pda-008-caracteristicas_produtos.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            db.execute(
                "INSERT OR REPLACE INTO plano VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (r["ID_PLANO"], r["CD_PLANO"], r["NM_PLANO"], _operadora(r["REGISTRO_OPERADORA"]), r["RAZAO_SOCIAL"],
                 r["VIGENCIA_PLANO"], r["CONTRATACAO"], r["SGMT_ASSISTENCIAL"], r["OBSTETRICIA"], r["ABRANGENCIA_COBERTURA"],
                 r["FATOR_MODERADOR"], r["ACOMODACAO_HOSPITALAR"], r["LIVRE_ESCOLHA"], r["SITUACAO_PLANO"], r["DT_SITUACAO"]),
            )
            if r["SITUACAO_PLANO"] in ("Ativo", "Suspenso"):
                ativos.add(r["ID_PLANO"])
        db.execute("INSERT INTO meta VALUES ('pda008_atualizacao', ?)", (r["DT_ATUALIZACAO"],))

    # Nota técnica: fica só a mais recente de cada (plano, nota), com as 10 faixas.
    recentes: dict[tuple[str, str], tuple[str, str, dict[int, tuple]]] = {}
    ordem_faixa = {f: i for i, f in enumerate(FAIXAS_ANS)}
    with zipfile.ZipFile(pasta_dados / "nota_tecnica_vcm_faixa_etaria.zip") as z:
        for membro in sorted(z.namelist()):
            with z.open(membro) as fh:
                for r in csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig"), delimiter=";"):
                    if r["ID_PLANO"] not in ativos or r["FAIXA_ETARIA"] not in ordem_faixa:
                        continue
                    chave = (r["ID_PLANO"], r["CD_NOTA"])
                    dt = _data_iso(r["DT_NTRP"])
                    atual = recentes.get(chave)
                    if atual is None or dt > atual[0]:
                        atual = recentes[chave] = (dt, r["ID_ABRG"], {})
                    if dt == atual[0]:
                        atual[2][ordem_faixa[r["FAIXA_ETARIA"]]] = (
                            float(r["VL_COMERCIAL_MENSALIDADE"]), float(r["VCM_MINIMO"]), float(r["VCM_MAXIMO"]))
    for (id_plano, cd_nota), (dt, abrg, faixas) in recentes.items():
        db.executemany(
            "INSERT INTO nota VALUES (?,?,?,?,?,?,?,?)",
            [(id_plano, cd_nota, dt, abrg, i, *v) for i, v in faixas.items()],
        )
    db.commit()
    db.close()
    return destino


class IndiceANS:
    """Consulta ao índice local da ANS, só de leitura.

    Uma conexão por thread: o SQLite não deixa uma conexão criada numa thread ser usada em outra, e o
    processamento em segundo plano (uploads, coleta) lê vários documentos ao mesmo tempo.
    """

    def __init__(self, caminho: Path):
        self.caminho = Path(caminho)
        self._local = threading.local()

    @property
    def db(self) -> sqlite3.Connection:
        db = getattr(self._local, "db", None)
        if db is None:
            db = sqlite3.connect(f"file:{self.caminho}?mode=ro", uri=True)
            db.row_factory = sqlite3.Row
            self._local.db = db
        return db

    def atualizado_em(self) -> str | None:
        r = self.db.execute("SELECT valor FROM meta WHERE chave='pda008_atualizacao'").fetchone()
        return r["valor"] if r else None

    def planos(self, cd_plano: str, registro_operadora: str | None = None) -> list[PlanoANS]:
        """Planos com esse nº de registro; vigentes (Ativo/Suspenso) primeiro."""
        sql = "SELECT * FROM plano WHERE cd_plano = ?"
        args = [cd_plano]
        if registro_operadora:
            sql += " AND registro_operadora = ?"
            args.append(_operadora(registro_operadora))
        linhas = self.db.execute(sql, args).fetchall()
        ordem = {"Ativo": 0, "Suspenso": 1}
        linhas = sorted(linhas, key=lambda r: (ordem.get(r["situacao"], 2), r["vigencia"] != "P"))
        return [
            PlanoANS(r["id_plano"], r["cd_plano"], r["nome"], r["registro_operadora"], r["operadora"], r["contratacao"],
                     r["segmentacao"], r["obstetricia"], r["abrangencia"], r["fator_moderador"], r["acomodacao"],
                     r["livre_escolha"], r["situacao"], r["dt_situacao"])
            for r in linhas
        ]

    def operadora(self, registro: str) -> dict | None:
        r = self.db.execute("SELECT * FROM operadora WHERE registro = ?", (_operadora(registro),)).fetchone()
        return dict(r) if r else None

    def operadoras_por_nome(self, trecho: str) -> list[dict]:
        like = f"%{trecho.upper()}%"
        rs = self.db.execute(
            "SELECT * FROM operadora WHERE upper(razao_social) LIKE ? OR upper(nome_fantasia) LIKE ? ORDER BY ativa DESC",
            (like, like),
        ).fetchall()
        return [dict(r) for r in rs]

    def ultima_nota(self, id_plano: str) -> str | None:
        """Data (AAAA-MM-DD) da nota técnica mais recente do plano."""
        linha = self.db.execute("SELECT MAX(dt_ntrp) FROM nota WHERE id_plano = ?", (id_plano,)).fetchone()
        return linha[0] if linha else None

    def notas_por_data(self, id_plano: str) -> dict[str, list[NotaTecnica]]:
        """As notas do plano agrupadas pela data de registro (uma por região quando o preço é regionalizado)."""
        por_data: dict[str, dict[str, NotaTecnica]] = {}
        for r in self.db.execute("SELECT * FROM nota WHERE id_plano = ? ORDER BY dt_ntrp, cd_nota, faixa", (id_plano,)):
            n = por_data.setdefault(r["dt_ntrp"], {}).setdefault(
                r["cd_nota"], NotaTecnica(r["cd_nota"], r["dt_ntrp"], r["abrangencia"], [None] * 10, [None] * 10, [None] * 10))
            n.vcm[r["faixa"]], n.minimo[r["faixa"]], n.maximo[r["faixa"]] = r["vcm"], r["minimo"], r["maximo"]
        return {d: list(notas.values()) for d, notas in por_data.items()}

    def notas_vigentes(self, id_plano: str, em: date | None = None) -> list[NotaTecnica]:
        """Notas da data mais recente do plano até `em`; material mais antigo que todas as notas usa a primeira."""
        por_data = self.notas_por_data(id_plano)
        if not por_data:
            return []
        datas = sorted(por_data)
        ate = [d for d in datas if em is None or d <= em.isoformat()]
        return por_data[ate[-1] if ate else datas[0]]
