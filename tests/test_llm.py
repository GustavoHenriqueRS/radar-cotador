"""Leitura por LLM sem rede: o pedido que os SDKs do Google e da OpenAI montam, o custo, a escolha do modelo e o replay."""
import base64
import io
import json
from dataclasses import asdict
from pathlib import Path

import httpx
import httpx2
import pdfplumber
import pytest

from leitor import llm
from leitor.esquema import LeituraDocumento

# O que o Gemini aceita em response_json_schema, segundo a documentação do SDK google-genai.
SUPORTADAS_GEMINI = {"$id", "$defs", "$ref", "$anchor", "type", "format", "title", "description", "enum", "items",
                     "prefixItems", "minItems", "maxItems", "minimum", "maximum", "anyOf", "oneOf", "properties",
                     "additionalProperties", "required", "propertyOrdering"}

LEITURA = {
    "operadora": "Unimed Guarulhos", "administradora": None, "tipo_contratacao": "coletivo_empresarial", "ufs": ["SP"],
    "vigencia_inicio": None, "vigencia_fim": None,
    "produtos": [{"id": "P1", "nome": "Essencial III", "registro_ans": "503.058/25-7", "acomodacao": "enfermaria",
                  "segmentacao": None, "abrangencia": None}],
    "tabelas": [{"pagina": 1, "titulo": "PME", "vidas_minimo": 2, "vidas_maximo": 29, "coparticipacao": "parcial",
                 "regiao": None, "preco_inclui": [],
                 "linhas": [{"produto_id": "P1", "coluna": "Essencial III", "valores": [116.56] + [None] * 9}]}],
    "coparticipacao": [], "carencias": [], "elegibilidade": [], "avisos": [],
}


PEDIDO = llm.PEDIDO.format(pagina=1, total=1)
GUARULHOS = Path(__file__).resolve().parent.parent / "amostras" / "publicas" / "unimed_guarulhos_pme_2026.pdf"


def _palavras_chave(schema):
    if isinstance(schema, list):
        for s in schema:
            yield from _palavras_chave(s)
    elif isinstance(schema, dict):
        for chave, valor in schema.items():
            yield chave
            if chave in ("properties", "$defs"):
                yield from _palavras_chave(list(valor.values()))
            elif chave in ("items", "anyOf", "oneOf", "prefixItems", "additionalProperties"):
                yield from _palavras_chave(valor)


@pytest.fixture
def gemini_falso(monkeypatch):
    """Troca a rede por uma resposta pronta e guarda o corpo exato que iria para a API."""
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    enviado = {"motivo": "STOP", "fila": [], "chamadas": 0}

    def handle_request(self, request):
        enviado["chamadas"] += 1
        if enviado["fila"]:
            status = enviado["fila"].pop(0)
            return httpx.Response(status, json={"error": {"code": status, "message": "cota", "status": "RESOURCE_EXHAUSTED"}})
        enviado["url"] = str(request.url)
        enviado["cabecalhos"] = dict(request.headers)
        enviado["corpo"] = json.loads(request.read())
        return httpx.Response(200, json={
            "candidates": [{"content": {"role": "model", "parts": [{"text": json.dumps(LEITURA)}]},
                            "finishReason": enviado["motivo"]}],
            "usageMetadata": {"promptTokenCount": 1000, "cachedContentTokenCount": 200,
                              "candidatesTokenCount": 3000, "thoughtsTokenCount": 500},
        })

    # No transporte, e não no Client.send, para o caminho real do httpx (cliente aberto, cabeçalhos) rodar.
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", handle_request)
    return enviado


@pytest.fixture
def openai_falso(monkeypatch):
    """Como o gemini_falso, no transporte do httpx2, que é o que o SDK da OpenAI usa."""
    monkeypatch.setenv("OPENAI_API_KEY", "chave-de-teste")
    enviado = {"status": "completed", "conteudo": {"type": "output_text", "text": json.dumps(LEITURA), "annotations": []},
               "fila": [], "chamadas": 0}

    def handle_request(self, request):
        enviado["chamadas"] += 1
        if enviado["fila"]:
            status = enviado["fila"].pop(0)
            return httpx2.Response(status, headers={"retry-after-ms": "10"}, json={"error": {"message": "cota"}})
        enviado["url"] = str(request.url)
        enviado["cabecalhos"] = dict(request.headers)
        enviado["corpo"] = json.loads(request.read())
        return httpx2.Response(200, json={
            "id": "resp_teste", "object": "response", "created_at": 0, "model": "gpt-6-luna",
            "status": enviado["status"],
            "incomplete_details": {"reason": "max_output_tokens"} if enviado["status"] == "incomplete" else None,
            "output": [{"type": "message", "id": "msg_teste", "role": "assistant", "status": "completed",
                        "content": [enviado["conteudo"]]}],
            "usage": {"input_tokens": 1000, "input_tokens_details": {"cached_tokens": 200, "cache_write_tokens": 0},
                      "output_tokens": 3000, "output_tokens_details": {"reasoning_tokens": 500}, "total_tokens": 4000},
        })

    monkeypatch.setattr(httpx2.HTTPTransport, "handle_request", handle_request)
    return enviado


def test_esquema_so_usa_o_que_o_gemini_aceita():
    usadas = set(_palavras_chave(LeituraDocumento.model_json_schema()))
    assert usadas <= SUPORTADAS_GEMINI, usadas - SUPORTADAS_GEMINI


def test_pedido_ao_gemini_leva_o_pdf_inteiro_e_o_esquema(gemini_falso):
    leitura, custo = llm._ler_gemini(b"%PDF-1.4 falso", "gemini-3.8-flash", "low", PEDIDO)

    assert gemini_falso["url"].endswith("/models/gemini-3.8-flash:generateContent")
    assert "key" not in gemini_falso["url"] and gemini_falso["cabecalhos"]["x-goog-api-key"] == "chave-de-teste"
    corpo = gemini_falso["corpo"]
    pdf, pedido = corpo["contents"][0]["parts"]
    assert pdf["inlineData"]["mime_type"] == "application/pdf"
    assert base64.b64decode(pdf["inlineData"]["data"]) == b"%PDF-1.4 falso"
    assert pedido["text"] == PEDIDO
    assert corpo["systemInstruction"]["parts"][0]["text"] == llm.PROMPT_SISTEMA
    config = corpo["generationConfig"]
    assert config["responseMimeType"] == "application/json"
    assert config["responseJsonSchema"] == LeituraDocumento.model_json_schema()
    assert config["thinkingConfig"]["thinking_level"] == "LOW"

    assert leitura.tabelas[0].linhas[0].valores[0] == 116.56
    assert (custo.entrada, custo.cache_leitura, custo.saida, custo.raciocinio) == (800, 200, 3500, 500)
    assert custo.usd == pytest.approx((800 * 0.75 + 200 * 0.075 + 3500 * 3.75) / 1e6)


@pytest.mark.parametrize("motivo, mensagem", [("MAX_TOKENS", "limite de tokens"), ("SAFETY", "interrompida")])
def test_resposta_incompleta_nao_vira_leitura(gemini_falso, motivo, mensagem):
    gemini_falso["motivo"] = motivo
    with pytest.raises(RuntimeError, match=mensagem):
        llm._ler_gemini(b"%PDF-1.4 falso", "gemini-3.8-flash", "low", PEDIDO)


def test_pedido_a_openai_leva_o_pdf_inteiro_e_o_esquema_estrito(openai_falso):
    leitura, custo = llm._ler_openai(b"%PDF-1.4 falso", "gpt-6-luna", "low", PEDIDO)

    assert openai_falso["url"] == "https://api.openai.com/v1/responses"
    assert openai_falso["cabecalhos"]["authorization"] == "Bearer chave-de-teste"
    corpo = openai_falso["corpo"]
    arquivo, pedido = corpo["input"][0]["content"]
    assert arquivo["type"] == "input_file" and arquivo["filename"] == "material.pdf"
    prefixo = "data:application/pdf;base64,"
    assert arquivo["file_data"].startswith(prefixo)
    assert base64.b64decode(arquivo["file_data"][len(prefixo):]) == b"%PDF-1.4 falso"
    assert pedido == {"type": "input_text", "text": PEDIDO}
    assert corpo["instructions"] == llm.PROMPT_SISTEMA
    formato = corpo["text"]["format"]
    assert formato["type"] == "json_schema" and formato["strict"] is True
    assert set(formato["schema"]["properties"]) == set(LeituraDocumento.model_fields)
    assert corpo["reasoning"] == {"effort": "low"} and corpo["store"] is False

    assert leitura.tabelas[0].linhas[0].valores[0] == 116.56
    assert (custo.entrada, custo.cache_leitura, custo.saida, custo.raciocinio) == (800, 200, 3000, 500)
    assert custo.usd == pytest.approx((800 * 0.10 + 200 * 0.01 + 3000 * 0.50) / 1e6)


def test_openai_incompleta_ou_recusada_nao_vira_leitura(openai_falso):
    openai_falso["status"] = "incomplete"
    with pytest.raises(RuntimeError, match="limite de tokens"):
        llm._ler_openai(b"%PDF-1.4 falso", "gpt-6-luna", "low", PEDIDO)
    openai_falso["status"] = "completed"
    openai_falso["conteudo"] = {"type": "refusal", "refusal": "não posso ajudar"}
    with pytest.raises(llm.LeituraRecusada, match="não posso ajudar"):
        llm._ler_openai(b"%PDF-1.4 falso", "gpt-6-luna", "low", PEDIDO)


def test_modelo_segue_a_chave_do_ambiente(monkeypatch):
    for variavel in ("LEITOR_MODELO", "GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(variavel, raising=False)
    assert llm.modelo_padrao() == "gpt-6-luna" and not llm.tem_credencial()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    assert llm.modelo_padrao() == "claude-opus-5" and llm.tem_credencial()
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    assert llm.modelo_padrao() == "gemini-3.8-flash"
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    assert llm.modelo_padrao() == "gpt-6-luna"
    monkeypatch.setenv("LEITOR_MODELO", "claude-sonnet-5")
    assert llm.modelo_padrao() == "claude-sonnet-5"


def test_modelo_sem_preco_nao_chega_a_chamar_a_api(tmp_path, gemini_falso):
    pdf = tmp_path / "tabela.pdf"
    pdf.write_bytes(b"%PDF-1.4 falso")
    with pytest.raises(ValueError, match="sem preço"):
        llm.ler_com_llm(pdf, modelo="gemini-9-ultra")
    assert "url" not in gemini_falso


def test_replay_prefere_o_modelo_padrao_e_depois_a_gravacao_mais_recente(monkeypatch, tmp_path):
    monkeypatch.setattr(llm, "PASTA_GRAVACOES", tmp_path)
    monkeypatch.setenv("LEITOR_MODELO", "gpt-6-luna")
    pdf = tmp_path / "tabela.pdf"
    pdf.write_bytes(b"%PDF-1.4 falso")
    sha = llm._sha256(pdf)
    for modelo, quando in (("claude-opus-5", "2026-09-01T12:00:00+00:00"), ("gemini-3.8-flash", "2026-09-30T12:00:00+00:00")):
        (tmp_path / f"{sha[:16]}_{modelo}.json").write_text(json.dumps({
            "gravada_em": quando, "custo": asdict(llm.Custo(modelo, 1, 1, 0, 0, 0.0)), "leitura": LEITURA}))

    assert llm.tem_gravacao(pdf) and not llm.tem_gravacao(pdf, "claude-sonnet-5")
    assert llm.ler_com_llm(pdf, replay=True).custo.modelo == "gemini-3.8-flash"
    assert llm.ler_com_llm(pdf, modelo="claude-opus-5", replay=True).custo.modelo == "claude-opus-5"
    (tmp_path / f"{sha[:16]}_gpt-6-luna.json").write_text(json.dumps({
        "gravada_em": "2026-08-01T12:00:00+00:00", "custo": asdict(llm.Custo("gpt-6-luna", 1, 1, 0, 0, 0.0)), "leitura": LEITURA}))
    assert llm.ler_com_llm(pdf, replay=True).custo.modelo == "gpt-6-luna"


def test_cada_pagina_vira_um_pdf_com_a_camada_de_texto():
    if not GUARULHOS.exists():
        pytest.skip("amostra ausente")
    paginas = llm._paginas(GUARULHOS.read_bytes())
    assert len(paginas) == 3
    for numero, pagina in enumerate(paginas, start=1):
        with pdfplumber.open(io.BytesIO(pagina)) as pdf:
            assert len(pdf.pages) == 1
            assert "TABELA DE VENDAS" in pdf.pages[0].extract_text()


def _leitura_da_pagina(pagina: int) -> LeituraDocumento:
    dados = json.loads(json.dumps(LEITURA))
    dados["tabelas"][0]["linhas"][0]["valores"][0] = 100.0 + pagina
    dados["avisos"] = [f"aviso {pagina}"]
    dados["carencias"] = [{"cobertura": "consultas", "prazo_dias": 30, "observacao": None}]
    return LeituraDocumento.model_validate(dados)


def test_leitura_por_pagina_junta_tudo_num_documento(monkeypatch, tmp_path):
    if not GUARULHOS.exists():
        pytest.skip("amostra ausente")
    monkeypatch.setattr(llm, "PASTA_GRAVACOES", tmp_path)
    pedidos = []

    def falso(pdf, modelo, esforco, pedido):
        pedidos.append(pedido)
        pagina = int(pedido.split("página ")[1].split(" ")[0])
        return _leitura_da_pagina(pagina), llm.Custo(modelo, 1000, 200, 0, 0, llm._usd(modelo, 1000, 200), 50)

    monkeypatch.setattr(llm, "_ler_openai", falso)
    r = llm.ler_com_llm(GUARULHOS, modelo="gpt-6-luna", esforco="low")

    assert sorted(pedidos) == [llm.PEDIDO.format(pagina=n, total=3) for n in (1, 2, 3)]
    assert [t.pagina for t in r.leitura.tabelas] == [1, 2, 3]
    assert [t.linhas[0].valores[0] for t in r.leitura.tabelas] == [101.0, 102.0, 103.0]
    assert [p.id for p in r.leitura.produtos] == ["p1.P1", "p2.P1", "p3.P1"]
    assert {linha.produto_id for t in r.leitura.tabelas for linha in t.linhas} == {"p1.P1", "p2.P1", "p3.P1"}
    assert len(r.leitura.carencias) == 1 and r.leitura.avisos == ["p. 1: aviso 1", "p. 2: aviso 2", "p. 3: aviso 3"]
    assert r.leitura.operadora == "Unimed Guarulhos"
    assert (r.custo.entrada, r.custo.saida, r.custo.raciocinio) == (3000, 600, 150)
    assert r.custo.usd == pytest.approx(3 * (1000 * 0.10 + 200 * 0.50) / 1e6)
    assert llm.ler_com_llm(GUARULHOS, replay=True).leitura == r.leitura


def test_limite_de_taxa_repete_a_pagina_em_vez_de_perder_a_leitura(gemini_falso, openai_falso):
    gemini_falso["fila"] = [429, 503]
    leitura, _ = llm._ler_gemini(b"%PDF-1.4 falso", "gemini-3.8-flash", "low", PEDIDO)
    assert gemini_falso["chamadas"] == 3 and leitura.tabelas

    openai_falso["fila"] = [429, 500]
    leitura, _ = llm._ler_openai(b"%PDF-1.4 falso", "gpt-6-luna", "low", PEDIDO)
    assert openai_falso["chamadas"] == 3 and leitura.tabelas
