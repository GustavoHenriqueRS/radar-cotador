"""Esquema da leitura por LLM (saída estruturada validada pelo pydantic)."""
from typing import Literal

from pydantic import BaseModel, Field


class Produto(BaseModel):
    id: str = Field(description="Identificador curto criado por você: P1, P2, ...")
    nome: str = Field(description="Nome comercial como aparece no documento")
    registro_ans: str | None = Field(description="Nº de registro ANS impresso para o produto (ex.: 503.058/25-7); null se não houver")
    acomodacao: Literal["enfermaria", "apartamento", "sem_internacao", "nao_informado"]
    segmentacao: str | None = Field(description="Ex.: 'Ambulatorial + Hospitalar com obstetrícia'")
    abrangencia: str | None = Field(description="Ex.: municipal, grupo de municípios, estadual, nacional")


class LinhaDePreco(BaseModel):
    produto_id: str
    coluna: str = Field(description="Rótulo da coluna como impresso (produto, região ou variação)")
    valores: list[float | None] = Field(
        description="Exatamente 10 valores na ordem 0–18, 19–23, 24–28, 29–33, 34–38, 39–43, 44–48, 49–53, 54–58, 59+; "
        "null na faixa que a tabela não vende"
    )


class TabelaDePreco(BaseModel):
    pagina: int = Field(description="Página do PDF, começando em 1")
    titulo: str = Field(description="Condição da tabela como impressa, ex.: 'Tabela de vendas 02 a 29 vidas — coparticipação parcial'")
    vidas_minimo: int | None
    vidas_maximo: int | None
    coparticipacao: Literal["sem", "parcial", "total", "com", "nao_informado"]
    regiao: str | None
    preco_inclui: list[str] = Field(description="Outros produtos ou taxas embutidos no preço (ex.: ['odonto']); vazio se é só o plano")
    linhas: list[LinhaDePreco]


class RegraCoparticipacao(BaseModel):
    procedimento: str
    regra: str = Field(description="Como impresso, ex.: '30% com limite de R$ 20,00', 'isento', 'R$ 25,00'")
    produtos: list[str] = Field(description="ids dos produtos a que se aplica; vazio = todos")


class Carencia(BaseModel):
    cobertura: str
    prazo_dias: int | None = Field(description="Prazo em dias (24 horas = 1)")
    observacao: str | None


class LeituraDocumento(BaseModel):
    operadora: str | None
    administradora: str | None = Field(description="Administradora de benefícios, se o material for dela")
    tipo_contratacao: Literal["individual_familiar", "coletivo_empresarial", "coletivo_adesao", "nao_informado"]
    ufs: list[str]
    vigencia_inicio: str | None = Field(description="AAAA-MM-DD")
    vigencia_fim: str | None = Field(description="AAAA-MM-DD")
    produtos: list[Produto]
    tabelas: list[TabelaDePreco]
    coparticipacao: list[RegraCoparticipacao]
    carencias: list[Carencia]
    elegibilidade: list[str] = Field(description="Adesão: entidades ou profissões elegíveis, resumidas")
    avisos: list[str] = Field(description="Dúvidas de leitura: cabeçalho ambíguo, coluna cortada, valor ilegível")
