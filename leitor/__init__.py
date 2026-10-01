"""Leitor de tabelas de venda de planos de saúde.

Duas leituras independentes do mesmo PDF (geométrica e por LLM), conferidas
entre si e contra os dados abertos da ANS.
"""
import os
from pathlib import Path


def carregar_env(arquivo: Path = Path(__file__).resolve().parent.parent / ".env"):
    """Lê as chaves de API e afins de um .env local, sem sobrescrever o ambiente."""
    if not arquivo.exists():
        return
    for linha in arquivo.read_text().splitlines():
        chave, sep, valor = linha.strip().partition("=")
        if sep and chave and not chave.startswith("#"):
            os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))
