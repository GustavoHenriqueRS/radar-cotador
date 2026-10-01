"""Uso: python -m leitor.cli amostras/publicas/arquivo.pdf [--llm | --replay] [--modelo gpt-6-luna] [--esforco low]"""
import argparse
import json
from pathlib import Path

from . import carregar_env
from .ans import IndiceANS, construir_indice
from .conferencia import Conferencia, conferir
from .faixas import formatar_registro
from .llm import LeituraLLM, ler_com_llm

RAIZ = Path(__file__).resolve().parent.parent
DADOS_ANS = RAIZ / "dados" / "ans"


def carregar_indice() -> IndiceANS:
    caminho = DADOS_ANS / "indice.sqlite"
    if not caminho.exists():
        print("Construindo o índice local da ANS (uma vez só)...")
        construir_indice(DADOS_ANS, caminho)
    return IndiceANS(caminho)


def imprimir(conf: Conferencia, llm: LeituraLLM | None = None):
    r = conf.resumo()
    print(f"\n{conf.arquivo}")
    geometrica = "geométrica sobre OCR" if conf.ocr else "geométrica"
    modo = f"dupla leitura ({geometrica} + LLM" + (", gravada" if llm and llm.replay else "") + ")" if conf.leitura_llm else f"leitura {geometrica}"
    print(f"  modo: {modo}")
    if llm:
        c = llm.custo
        tempo = f"; {llm.segundos:.0f} s" if llm.segundos else ""
        print(f"  custo LLM: US$ {c.usd:.4f} ({c.modelo}, esforço {llm.esforco}; {c.entrada + c.cache_escrita + c.cache_leitura} tokens "
              f"de entrada, {c.saida} de saída, {c.raciocinio} deles de raciocínio{tempo})")
    print(f"  {r['celulas']} preços em {r['colunas']} colunas ({r['colunas_com_registro_ans']} com registro ANS)")
    inicio, fim = conf.vigencia_impressa
    if inicio:
        print(f"  vigência impressa: {inicio:%d/%m/%Y}" + (f" a {fim:%d/%m/%Y}" if fim else ""))
    if conf.leitura_llm:
        print(f"  confirmados pelas duas leituras: {r['confirmado']} | por uma leitura e o cálculo: {r['confirmado_calculo']} | "
              f"divergentes: {r['divergente']} | só geométrica: {r['so_geometrico']} | só LLM: {r['so_llm']}")
    else:
        print(f"  confirmados pelo cálculo do padrão de faixas: {r['confirmado_calculo']}")
    print(f"  para revisão humana: {r['revisar']} de {r['celulas']} | erros: {r['erros']} | alertas: {r['alertas']}")
    vistos = set()
    for col in conf.colunas:
        for a in col.achados:
            if a.severidade == "info":
                continue
            chave = (col.registro, a.regra, a.mensagem)
            if chave in vistos:
                continue
            vistos.add(chave)
            reg = formatar_registro(col.registro) if col.registro else "sem registro"
            print(f"   [{a.severidade}] p{col.pagina} {reg} {col.coluna[:30]!r}: {a.mensagem}")
    for a in conf.achados_documento:
        print(f"   [{a.severidade}] documento: {a.mensagem}")


def salvar(conf: Conferencia, destino: Path):
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps({
        "arquivo": conf.arquivo,
        "resumo": conf.resumo(),
        "leitura_llm": conf.leitura_llm.model_dump() if conf.leitura_llm else None,
        "colunas": [c.como_dict() for c in conf.colunas],
        "achados_documento": [a.como_dict() for a in conf.achados_documento],
    }, ensure_ascii=False, indent=1))


def main():
    ap = argparse.ArgumentParser(description="Lê tabelas de venda de planos de saúde e confere contra a ANS.")
    ap.add_argument("pdfs", nargs="+", type=Path)
    grupo = ap.add_mutually_exclusive_group()
    grupo.add_argument("--llm", action="store_true", help="faz a segunda leitura por LLM (GPT, Gemini ou Claude, conforme a chave no .env)")
    grupo.add_argument("--replay", action="store_true", help="usa a leitura por LLM gravada anteriormente")
    ap.add_argument("--modelo", help="padrão: LEITOR_MODELO, ou gpt-6-luna")
    ap.add_argument("--esforco", help="nível de raciocínio: low, medium, high")
    args = ap.parse_args()

    carregar_env()
    indice = carregar_indice()
    totais = {"usd": 0.0, "celulas": 0, "confirmado": 0, "confirmado_calculo": 0, "divergente": 0, "so_geometrico": 0, "so_llm": 0, "falhas": 0}
    for pdf in args.pdfs:
        llm = None
        if args.llm or args.replay:
            try:
                llm = ler_com_llm(pdf, modelo=args.modelo, esforco=args.esforco, replay=args.replay)
            except Exception as e:
                print(f"\n{pdf.name}\n  falha na leitura por LLM: {type(e).__name__}: {e}")
                totais["falhas"] += 1
                continue
        conf = conferir(pdf, indice, llm.leitura if llm else None)
        imprimir(conf, llm)
        salvar(conf, RAIZ / "saidas" / f"{pdf.stem}.json")
        if llm:
            r = conf.resumo()
            totais["usd"] += llm.custo.usd
            for chave in ("celulas", "confirmado", "confirmado_calculo", "divergente", "so_geometrico", "so_llm"):
                totais[chave] += r[chave]

    if (args.llm or args.replay) and len(args.pdfs) > 1:
        t = totais
        print(f"\nTotal: {len(args.pdfs) - t['falhas']} PDFs lidos, {t['falhas']} falhas, US$ {t['usd']:.4f}")
        print(f"  {t['celulas']} preços | confirmados: {t['confirmado']} | por uma leitura e o cálculo: {t['confirmado_calculo']} | divergentes: {t['divergente']} | "
              f"só geométrica: {t['so_geometrico']} | só LLM: {t['so_llm']}")


if __name__ == "__main__":
    main()
