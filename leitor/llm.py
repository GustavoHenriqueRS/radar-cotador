"""Segunda leitura do PDF por LLM (Gemini, GPT ou Claude), com saída estruturada e custo medido.

Cada página vai como um PDF de uma página só: o provedor extrai o texto nativo e vê a página como
imagem (não há conversão para PNG/JPEG deste lado). Ler página por página, em paralelo, mantém cada
resposta curta. Numa chamada só com o documento inteiro, os modelos menores resumem e pulam tabelas
(e avisam que pularam), o que tira da dupla leitura justamente os documentos grandes.

Cada leitura real fica gravada em `amostras/leituras_llm/`, para a demonstração rodar de novo
sem chave de API (modo replay, sempre identificado como tal).
"""
import base64
import hashlib
import io
import json
import os
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .esquema import LeituraDocumento
from .pdf import TRAVA_PDFIUM

# As leituras do acervo de demonstração ficam no repositório; as de material coletado ou enviado, na pasta de
# dados (LEITOR_GRAVACOES), e também servem de cache: o mesmo PDF nunca é lido duas vezes.
ACERVO_GRAVADO = Path(__file__).resolve().parent.parent / "amostras" / "leituras_llm"
PASTA_GRAVACOES = Path(os.environ.get("LEITOR_GRAVACOES") or ACERVO_GRAVADO)
PAGINAS_EM_PARALELO = 8
# Tentativas por página em limite de taxa (429) e erro transitório (5xx), com espera exponencial.
TENTATIVAS = 5

# US$ por milhão de tokens: entrada, entrada lida de cache, saída (o raciocínio é cobrado como saída).
# A escrita de cache só é cobrada à parte no Claude, a 125% da entrada.
PRECOS = {
    # Preço promocional do Google até 31/12/2026; a partir de 2027, US$ 1,50 / 7,50.
    "gemini-3.8-flash": (0.75, 0.075, 3.75),
    "gemini-3.5-flash-lite": (0.30, 0.03, 2.50),
    "gpt-6-luna": (0.10, 0.01, 0.50),
    "gpt-5.6-luna": (0.20, 0.02, 1.20),
    "gpt-6.1-sol": (2.00, 0.10, 10.00),
    "gpt-6-sol": (2.00, 0.20, 10.00),
    "claude-opus-5": (5.00, 0.50, 25.00),
    "claude-sonnet-5": (2.00, 0.20, 10.00),
    "claude-haiku-4-5": (1.00, 0.10, 5.00),
}
CHAVES = {"gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"), "openai": ("OPENAI_API_KEY",), "anthropic": ("ANTHROPIC_API_KEY",)}
# Em ordem de preferência: o GPT-6 Luna leu o acervo inteiro com o menor custo medido.
PADRAO_POR_PROVEDOR = {"openai": "gpt-6-luna", "gemini": "gemini-3.8-flash", "anthropic": "claude-opus-5"}
ESFORCO_PADRAO = {"gemini": "low", "openai": "low", "anthropic": "high"}

PROMPT_SISTEMA = """\
Você transcreve páginas de materiais de venda de planos de saúde (tabelas de preço de operadoras e \
de administradoras de benefícios) para o esquema JSON, exatamente como estão impressas.

Regras:
1. Transcreva todas as tabelas de preço da página, sem resumir nem omitir nenhuma: a transcrição é \
conferida célula a célula com outra leitura, e o que faltar vira trabalho manual.
2. Transcreva, não calcule nem corrija. Cada preço é o número impresso (R$ 1.065,14 → 1065.14). \
Valor ilegível ou ausente vira null, com a explicação em `avisos`.
3. Faixas etárias: sempre as 10 da ANS, nesta ordem: 0–18, 19–23, 24–28, 29–33, 34–38, 39–43, \
44–48, 49–53, 54–58, 59+. `valores` tem sempre 10 posições; use null nas faixas que a tabela não \
vende (ex.: plano sênior a partir de 44 anos).
4. Uma `TabelaDePreco` para cada condição de venda (combinação de número de vidas, coparticipação e \
região). Grades lado a lado são tabelas diferentes; uma grade que junta condições (ex.: colunas de \
coparticipação parcial e de coparticipação total) se divide por condição. Uma grade impressa de novo \
para outra entidade, região ou grupo é outra tabela e também se transcreve.
5. Cada coluna de preço impressa vira uma `LinhaDePreco`, em uma única tabela. Se as colunas são \
produtos, `coluna` é o nome do produto; se são regiões ou variações de um mesmo produto, `coluna` é \
o rótulo impresso e `produto_id` aponta o produto.
6. Associe cada produto ao nº de registro ANS impresso sobre a sua coluna (formato NNN.NNN/AA-D). \
Cabeçalhos quebrados em duas linhas são comuns: use o alinhamento vertical. Na dúvida, explique em \
`avisos`.
7. `preco_inclui`: marque quando o preço embute outro produto ou taxa (ex.: "Com Odonto", \
"taxa associativa inclusa").
8. Coparticipação, carências e elegibilidade: registre fielmente o que está impresso, sem completar \
com conhecimento externo.
9. Datas no formato AAAA-MM-DD.
"""
PEDIDO = ("Esta é a página {pagina} de {total} do material. Transcreva todas as tabelas de preço desta "
          "página; nos demais campos, só o que estiver impresso nela.")
LIMITE_DE_SAIDA = "a página passou do limite de tokens de saída"


@dataclass
class Custo:
    modelo: str
    entrada: int
    saida: int
    cache_escrita: int
    cache_leitura: int
    usd: float
    raciocinio: int = 0


@dataclass
class LeituraLLM:
    leitura: LeituraDocumento
    custo: Custo
    gravada_em: str
    replay: bool
    sha256_pdf: str
    esforco: str | None = None
    segundos: float | None = None


class LeituraRecusada(RuntimeError):
    pass


def provedor(modelo: str) -> str:
    if modelo.startswith("gemini"):
        return "gemini"
    return "openai" if modelo.startswith("gpt") else "anthropic"


def tem_credencial(modelo: str | None = None) -> bool:
    return any(os.environ.get(v) for v in CHAVES[provedor(modelo or modelo_padrao())])


def modelo_padrao() -> str:
    """LEITOR_MODELO manda; sem ele, vale o primeiro provedor com chave no ambiente."""
    if os.environ.get("LEITOR_MODELO"):
        return os.environ["LEITOR_MODELO"]
    return next((m for m in PADRAO_POR_PROVEDOR.values() if tem_credencial(m)), PADRAO_POR_PROVEDOR["openai"])


def _preco(modelo: str) -> tuple[float, float, float] | None:
    return next((PRECOS[nome] for nome in sorted(PRECOS, key=len, reverse=True) if modelo.startswith(nome)), None)


def _usd(modelo: str, entrada: int, saida: int, cache_escrita: int = 0, cache_leitura: int = 0) -> float:
    entrada_pm, cache_pm, saida_pm = _preco(modelo)
    return (entrada * entrada_pm + cache_escrita * entrada_pm * 1.25 + cache_leitura * cache_pm + saida * saida_pm) / 1_000_000


def _ler_gemini(pdf: bytes, modelo: str, esforco: str, pedido: str) -> tuple[LeituraDocumento, Custo]:
    from google import genai
    from google.genai import types

    with genai.Client(http_options=types.HttpOptions(retry_options=types.HttpRetryOptions(attempts=TENTATIVAS))) as cliente:
        resposta = cliente.models.generate_content(
            model=modelo,
            contents=[types.Part.from_bytes(data=pdf, mime_type="application/pdf"), pedido],
            config=types.GenerateContentConfig(
                system_instruction=PROMPT_SISTEMA,
                response_mime_type="application/json",
                response_json_schema=LeituraDocumento.model_json_schema(),
                thinking_config=types.ThinkingConfig(thinking_level=esforco),
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
    if not resposta.candidates:
        raise LeituraRecusada(f"leitura bloqueada: {resposta.prompt_feedback}")
    motivo = resposta.candidates[0].finish_reason
    if motivo == types.FinishReason.MAX_TOKENS:
        raise RuntimeError(LIMITE_DE_SAIDA)
    if motivo != types.FinishReason.STOP:
        raise LeituraRecusada(f"leitura interrompida: {motivo}")
    leitura = LeituraDocumento.model_validate_json(resposta.text)

    uso = resposta.usage_metadata
    cache = uso.cached_content_token_count or 0
    entrada = (uso.prompt_token_count or 0) - cache
    raciocinio = uso.thoughts_token_count or 0
    saida = (uso.candidates_token_count or 0) + raciocinio
    return leitura, Custo(modelo, entrada, saida, 0, cache, _usd(modelo, entrada, saida, 0, cache), raciocinio)


def _ler_openai(pdf: bytes, modelo: str, esforco: str, pedido: str) -> tuple[LeituraDocumento, Custo]:
    from openai import OpenAI

    with OpenAI(max_retries=TENTATIVAS - 1) as cliente:
        resposta = cliente.responses.parse(
            model=modelo,
            instructions=PROMPT_SISTEMA,
            input=[{
                "role": "user",
                "content": [
                    # Nome neutro: o nome do arquivo (operadora, data) não pode servir de pista para a leitura.
                    {"type": "input_file", "filename": "material.pdf",
                     "file_data": "data:application/pdf;base64," + base64.b64encode(pdf).decode()},
                    {"type": "input_text", "text": pedido},
                ],
            }],
            text_format=LeituraDocumento,
            reasoning={"effort": esforco},
            store=False,
        )
    if resposta.status == "incomplete":
        motivo = resposta.incomplete_details.reason if resposta.incomplete_details else None
        if motivo == "max_output_tokens":
            raise RuntimeError(LIMITE_DE_SAIDA)
        raise LeituraRecusada(f"leitura interrompida: {motivo}")
    recusa = next((c.refusal for item in resposta.output if item.type == "message"
                   for c in item.content if c.type == "refusal"), None)
    if recusa:
        raise LeituraRecusada(f"leitura recusada: {recusa}")
    leitura = resposta.output_parsed
    if leitura is None:
        raise RuntimeError("a resposta veio sem o JSON do esquema")

    uso = resposta.usage
    cache = uso.input_tokens_details.cached_tokens or 0
    entrada = uso.input_tokens - cache
    raciocinio = uso.output_tokens_details.reasoning_tokens or 0
    return leitura, Custo(modelo, entrada, uso.output_tokens, 0, cache, _usd(modelo, entrada, uso.output_tokens, 0, cache), raciocinio)


def _ler_claude(pdf: bytes, modelo: str, esforco: str, pedido: str) -> tuple[LeituraDocumento, Custo]:
    import anthropic

    client = anthropic.Anthropic()
    with client.beta.messages.stream(
        model=modelo,
        max_tokens=64000,
        # Em caso de recusa pelos classificadores de segurança, a API refaz a chamada no modelo recomendado.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=[{"type": "text", "text": PROMPT_SISTEMA, "cache_control": {"type": "ephemeral"}}],
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {"type": "base64", "media_type": "application/pdf", "data": base64.standard_b64encode(pdf).decode()},
                },
                {"type": "text", "text": pedido},
            ],
        }],
        output_format=LeituraDocumento,
        output_config={"effort": esforco},
    ) as stream:
        mensagem = stream.get_final_message()

    if mensagem.stop_reason == "refusal":
        raise LeituraRecusada(f"leitura recusada: {mensagem.stop_details}")
    if mensagem.stop_reason == "max_tokens":
        raise RuntimeError(LIMITE_DE_SAIDA)
    leitura = getattr(mensagem, "parsed_output", None)
    if leitura is None:
        texto = next(b.text for b in mensagem.content if b.type == "text")
        leitura = LeituraDocumento.model_validate_json(texto)

    uso = mensagem.usage
    escrita = uso.cache_creation_input_tokens or 0
    lida = uso.cache_read_input_tokens or 0
    # Se o fallback do servidor trocou o modelo, cobra-se o que respondeu; sem preço cadastrado, estima-se pelo pedido.
    cobrado = mensagem.model if _preco(mensagem.model) else modelo
    usd = _usd(cobrado, uso.input_tokens, uso.output_tokens, escrita, lida)
    return leitura, Custo(mensagem.model, uso.input_tokens, uso.output_tokens, escrita, lida, usd)


def _paginas(pdf: bytes) -> list[bytes]:
    """Cada página como um PDF próprio, com a camada de texto preservada."""
    import pypdfium2 as pdfium

    with TRAVA_PDFIUM:
        origem = pdfium.PdfDocument(pdf)
        try:
            paginas = []
            for i in range(len(origem)):
                pagina = pdfium.PdfDocument.new()
                pagina.import_pages(origem, [i])
                saida = io.BytesIO()
                pagina.save(saida)
                pagina.close()
                paginas.append(saida.getvalue())
            return paginas
        finally:
            origem.close()


def _mais_comum(valores):
    contagem = Counter(v for v in valores if v)
    return contagem.most_common(1)[0][0] if contagem else None


def _sem_repetir(itens: list) -> list:
    return list({item.model_dump_json(): item for item in itens}.values())


def juntar_paginas(por_pagina: list[tuple[int, LeituraDocumento]]) -> LeituraDocumento:
    """A leitura do documento a partir das leituras de cada página; o id de produto ganha a página como prefixo."""
    produtos, tabelas, coparticipacao, carencias, elegibilidade, avisos = [], [], [], [], [], []
    for pagina, lt in por_pagina:
        produtos += [p.model_copy(update={"id": f"p{pagina}.{p.id}"}) for p in lt.produtos]
        for t in lt.tabelas:
            linhas = [linha.model_copy(update={"produto_id": f"p{pagina}.{linha.produto_id}"}) for linha in t.linhas]
            tabelas.append(t.model_copy(update={"pagina": pagina, "linhas": linhas}))
        coparticipacao += [c.model_copy(update={"produtos": [f"p{pagina}.{x}" for x in c.produtos]}) for c in lt.coparticipacao]
        carencias += lt.carencias
        elegibilidade += lt.elegibilidade
        avisos += [f"p. {pagina}: {a}" for a in lt.avisos]
    leituras = [lt for _, lt in por_pagina]
    return LeituraDocumento(
        operadora=_mais_comum(lt.operadora for lt in leituras),
        administradora=_mais_comum(lt.administradora for lt in leituras),
        tipo_contratacao=_mais_comum(lt.tipo_contratacao for lt in leituras if lt.tipo_contratacao != "nao_informado") or "nao_informado",
        ufs=sorted({uf for lt in leituras for uf in lt.ufs}),
        vigencia_inicio=_mais_comum(lt.vigencia_inicio for lt in leituras),
        vigencia_fim=_mais_comum(lt.vigencia_fim for lt in leituras),
        produtos=produtos,
        tabelas=tabelas,
        coparticipacao=_sem_repetir(coparticipacao),
        carencias=_sem_repetir(carencias),
        elegibilidade=list(dict.fromkeys(elegibilidade)),
        avisos=avisos,
    )


def _somar(custos: list[Custo]) -> Custo:
    return Custo(
        modelo=custos[0].modelo,
        entrada=sum(c.entrada for c in custos),
        saida=sum(c.saida for c in custos),
        cache_escrita=sum(c.cache_escrita for c in custos),
        cache_leitura=sum(c.cache_leitura for c in custos),
        usd=round(sum(c.usd for c in custos), 6),
        raciocinio=sum(c.raciocinio for c in custos),
    )


def _sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def _arquivo_gravacao(sha: str, modelo: str) -> Path:
    return PASTA_GRAVACOES / f"{sha[:16]}_{modelo}.json"


def _gravacao(sha: str, modelo: str | None = None) -> Path | None:
    """A gravação do modelo pedido; sem modelo, a do modelo padrão e, na falta dela, a mais recente."""
    pastas = list(dict.fromkeys([PASTA_GRAVACOES, ACERVO_GRAVADO]))
    nomes = [f"{sha[:16]}_{modelo}.json"] if modelo else [f"{sha[:16]}_{modelo_padrao()}.json"]
    for pasta in pastas:
        for nome in nomes:
            if (pasta / nome).exists():
                return pasta / nome
    if modelo:
        return None
    candidatas = [p for pasta in pastas for p in pasta.glob(f"{sha[:16]}_*.json")]
    return max(candidatas, key=lambda p: json.loads(p.read_text())["gravada_em"], default=None)


def ler_com_llm(caminho_pdf: Path, modelo: str | None = None, esforco: str | None = None, replay: bool = False) -> LeituraLLM:
    sha = _sha256(caminho_pdf)
    if replay:
        gravacao = _gravacao(sha, modelo)
        if gravacao is None:
            raise FileNotFoundError(f"não há leitura gravada de {caminho_pdf.name}" + (f" com {modelo}" if modelo else ""))
        dados = json.loads(gravacao.read_text())
        return LeituraLLM(LeituraDocumento.model_validate(dados["leitura"]), Custo(**dados["custo"]), dados["gravada_em"],
                          True, sha, dados.get("esforco"), dados.get("segundos"))

    modelo = modelo or modelo_padrao()
    if _preco(modelo) is None:
        raise ValueError(f"sem preço cadastrado para {modelo}; inclua o modelo em PRECOS antes de gastar")
    esforco = esforco or os.environ.get("LEITOR_ESFORCO") or ESFORCO_PADRAO[provedor(modelo)]
    ler = {"gemini": _ler_gemini, "openai": _ler_openai, "anthropic": _ler_claude}[provedor(modelo)]
    paginas = _paginas(caminho_pdf.read_bytes())

    def ler_pagina(i: int):
        return ler(paginas[i], modelo, esforco, PEDIDO.format(pagina=i + 1, total=len(paginas)))

    inicio = time.monotonic()
    with ThreadPoolExecutor(PAGINAS_EM_PARALELO) as executor:
        resultados = list(executor.map(ler_pagina, range(len(paginas))))
    segundos = round(time.monotonic() - inicio, 1)
    leitura = juntar_paginas([(i + 1, lt) for i, (lt, _) in enumerate(resultados)])
    custo = _somar([c for _, c in resultados])

    gravada_em = datetime.now(timezone.utc).isoformat(timespec="seconds")
    PASTA_GRAVACOES.mkdir(parents=True, exist_ok=True)
    _arquivo_gravacao(sha, modelo).write_text(json.dumps({
        "arquivo": caminho_pdf.name,
        "sha256": sha,
        "gravada_em": gravada_em,
        "esforco": esforco,
        "paginas": len(paginas),
        "segundos": segundos,
        "custo": asdict(custo),
        "leitura": leitura.model_dump(),
    }, ensure_ascii=False, indent=1))
    return LeituraLLM(leitura, custo, gravada_em, False, sha, esforco, segundos)


def tem_gravacao(caminho_pdf: Path, modelo: str | None = None) -> bool:
    return _gravacao(_sha256(caminho_pdf), modelo) is not None
