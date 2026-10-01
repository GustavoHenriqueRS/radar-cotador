"""Regras de validação com base legal.

- RN 563/2022 (antiga RN 63/2003), art. 3º: faixas etárias.
- RN 564/2022, arts. 5º e 6º §2º: preço de venda dentro da banda da nota técnica (VCM ±30%).
- RN 543/2022: situação do plano (suspenso não aceita contrato novo).
- Lei 9.656/98, art. 12, V: prazos máximos de carência; art. 11: cobertura parcial temporária (CPT) de
  doença preexistente por até 24 meses.
"""
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from statistics import median

from .ans import IndiceANS, NotaTecnica, PlanoANS
from .faixas import FAIXAS

ERRO, ALERTA, INFO = "erro", "alerta", "info"


def _br(iso: str) -> str:
    """2025-12-23 → 23/12/2025"""
    return f"{iso[8:10]}/{iso[5:7]}/{iso[:4]}" if iso and len(iso) >= 10 else iso


@dataclass
class Achado:
    regra: str
    severidade: str
    mensagem: str
    faixas: list[str] = field(default_factory=list)

    def como_dict(self) -> dict:
        return {"regra": self.regra, "severidade": self.severidade, "mensagem": self.mensagem, "faixas": self.faixas}


def faixas_rn563(valores: list[float | None], tolerancia: float = 0.001, preco_composto: bool = False) -> list[Achado]:
    """Três regras do art. 3º. A tolerância absorve o arredondamento em centavos (as operadoras usam o limite exato).

    Se o preço embute outro produto ou taxa fixa (ex.: odonto), somar um valor constante a todas
    as faixas distorce as proporções e as regras I e II deixam de valer para o total: a violação
    aparente vira informação, e a conferência dessas células fica com a dupla leitura.
    """
    achados = []
    severidade = INFO if preco_composto else ERRO
    presentes = [(i, v) for i, v in enumerate(valores) if v is not None]
    for (i, a), (j, b) in zip(presentes, presentes[1:]):
        if b < a - 0.005:
            achados.append(Achado("RN 563 art. 3º III", ERRO, f"variação negativa: {FAIXAS[i]} R$ {a:.2f} → {FAIXAS[j]} R$ {b:.2f}", [FAIXAS[j]]))
    v1, v7, v10 = valores[0], valores[6], valores[9]
    if v1 is None or v7 is None or v10 is None:
        if v7 is not None and v10 is not None:
            achados.append(Achado("RN 563 art. 3º I/II", INFO, "produto sem as faixas iniciais (ex.: plano sênior): regras I e II não se aplicam"))
        return achados
    if v10 > 6 * v1 * (1 + tolerancia):
        achados.append(Achado("RN 563 art. 3º I", severidade, f"59+ custa {v10 / v1:.2f}× a faixa 0–18 (máximo 6×)", ["00-18", "59+"]))
    if v10 * v1 > v7 * v7 * (1 + tolerancia):
        achados.append(Achado(
            "RN 563 art. 3º II", severidade,
            f"variação 7ª→10ª ({v10 / v7 - 1:.1%}) maior que 1ª→7ª ({v7 / v1 - 1:.1%})"
            + (" — esperado: o preço inclui outro produto, então a regra não se aplica ao total" if preco_composto else ""),
            ["00-18", "44-48", "59+"],
        ))
    return achados


def _razoes(valores, nota: NotaTecnica) -> dict[int, float]:
    return {i: v / nota.vcm[i] for i, v in enumerate(valores) if v is not None and nota.vcm[i]}


def _dispersao(razoes: dict[int, float]) -> float:
    return (max(razoes.values()) / min(razoes.values()) - 1) if razoes else float("inf")


def referencia_ntrp(valores: list[float | None], notas: list[NotaTecnica], hoje: date | None = None,
                    tolerancia_pontual: float = 0.03, preco_composto: bool = False) -> list[Achado]:
    """Compara a tabela com o valor comercial da nota técnica (NTRP) do plano, faixa a faixa.

    - Desvio pontual: uma faixa foge da proporção das demais em relação ao VCM. É o sinal típico
      de erro de digitação ou de leitura, mesmo quando a tabela inteira já foi reajustada.
    - Abaixo da despesa assistencial: vedado pela RN 564 art. 5º.
    - Fora da banda ±30% (RN 564 art. 6º §2º): com nota de mais de um ano, é compatível com
      reajustes acumulados (a NTRP deveria ter sido atualizada); com nota recente, é alerta.
    Em preço regionalizado há uma nota por região: usa a que melhor explica a tabela.
    `hoje` é a data do material. Nota registrada depois dele não diz quanto o preço devia valer na época:
    os limites absolutos viram informação, e só o desvio pontual, que é proporção entre faixas, segue alerta.
    """
    if not notas:
        return [Achado("RN 564", INFO, "plano sem nota técnica de preço nos dados abertos (ex.: pós-estabelecido)")]
    nota = min(notas, key=lambda n: _dispersao(_razoes(valores, n)))
    razoes = _razoes(valores, nota)
    if not razoes:
        return []
    achados = []
    tipica = median(razoes.values())
    posterior = hoje is not None and date.fromisoformat(nota.dt_ntrp) > hoje
    for i, r in razoes.items():
        # Preço com outro produto embutido (valor fixo somado) não mantém a proporção com o VCM.
        if abs(r / tipica - 1) > tolerancia_pontual and not preco_composto:
            achados.append(Achado(
                "Nota técnica × tabela", ALERTA,
                f"{FAIXAS[i]}: R$ {valores[i]:.2f} = {r:.2f}× o VCM, enquanto as demais faixas ficam em ~{tipica:.2f}× "
                f"(nota {nota.cd_nota} de {_br(nota.dt_ntrp)}): faixa fora do padrão, conferir",
                [FAIXAS[i]],
            ))
    for i, v in enumerate(valores):
        if v is None or nota.minimo[i] is None or nota.vcm[i] is None:
            continue
        despesa_limita = nota.minimo[i] > 0.7 * nota.vcm[i] + 0.01
        if despesa_limita and v < nota.minimo[i] - 0.01:
            texto = (f"{FAIXAS[i]}: R$ {v:.2f} abaixo da despesa assistencial da nota {nota.cd_nota} de {_br(nota.dt_ntrp)} "
                     f"(mínimo R$ {nota.minimo[i]:.2f}; VCM R$ {nota.vcm[i]:.2f})")
            if posterior:
                achados.append(Achado("RN 564 art. 5º", INFO, texto + ": a nota é posterior ao material, só informativo"))
            else:
                achados.append(Achado("RN 564 art. 5º", ALERTA, texto, [FAIXAS[i]]))
    ja_apontadas = {f for a in achados for f in a.faixas}
    fora = [i for i, v in enumerate(valores)
            if v is not None and nota.minimo[i] is not None and FAIXAS[i] not in ja_apontadas
            and not (nota.minimo[i] - 0.01 <= v <= nota.maximo[i] + 0.01)]
    if fora:
        idade = ((hoje or date.today()) - date.fromisoformat(nota.dt_ntrp)).days
        lado = "acima" if tipica > 1 else "abaixo"
        texto = (f"tabela {abs(tipica - 1):.0%} {lado} do VCM da nota {nota.cd_nota} de {_br(nota.dt_ntrp)}, "
                 f"fora da banda de ±30% em {len(fora)} faixa(s)")
        if posterior:
            achados.append(Achado("RN 564 art. 6º §2º", INFO, texto + ": a nota é posterior ao material, só informativo"))
        elif idade > 365:
            achados.append(Achado("RN 564 art. 6º §2º", INFO, texto + ": compatível com reajustes acumulados desde a nota (NTRP desatualizada)"))
        else:
            achados.append(Achado("RN 564 art. 6º §2º", ALERTA, texto + ": a nota tem menos de um ano, conferir", [FAIXAS[i] for i in fora]))
    return achados


FOLGA_NOTA_NOVA = 30
# A data da nota na ANS é a do registro, que pode vir antes ou depois de a tabela começar a valer.
NOTAS_PLAUSIVEIS = (timedelta(days=365), timedelta(days=180))


def referencia_na_epoca(valores: list[float | None], notas_por_data: dict[str, list[NotaTecnica]], data_material: date | None,
                        preco_composto: bool = False) -> list[Achado]:
    """Confere a tabela contra a nota técnica que pode ter servido de base a ela.

    Sem a data do material, vale a nota mais recente, comparada com hoje. Com a data, são plausíveis as notas
    registradas de um ano antes a seis meses depois dela, e o alerta só fica quando nenhuma delas explica o
    preço: a dúvida sobre qual nota valia não manda ninguém revisar.
    """
    if not notas_por_data:
        return referencia_ntrp(valores, [])
    datas = sorted(notas_por_data)
    if data_material is None:
        return referencia_ntrp(valores, notas_por_data[datas[-1]], preco_composto=preco_composto)
    antes, depois = NOTAS_PLAUSIVEIS
    plausiveis = [d for d in datas if data_material - antes <= date.fromisoformat(d) <= data_material + depois]
    if not plausiveis:
        ate = [d for d in datas if d <= data_material.isoformat()]
        plausiveis = [ate[-1] if ate else datas[0]]
    resultados = [referencia_ntrp(valores, notas_por_data[d], hoje=data_material, preco_composto=preco_composto) for d in plausiveis]
    return min(reversed(resultados), key=lambda achados: sum(a.severidade != INFO for a in achados))


def nota_mais_nova(ultima_nota: str | None, data_material: date | None) -> list[Achado]:
    """A operadora registrou preço novo na ANS depois deste material: a tabela pode estar desatualizada.

    É informação, não erro de leitura: o preço lido está certo para a data dele. Na tabela publicada, o mesmo
    sinal vira aviso no radar para pedir a versão atual à fonte.
    """
    if not ultima_nota or not data_material:
        return []
    nota = date.fromisoformat(ultima_nota)
    if (nota - data_material).days <= FOLGA_NOTA_NOVA:
        return []
    return [Achado("RN 564 (nota nova)", INFO,
                   f"a operadora registrou nota técnica nova em {nota:%d/%m/%Y}, depois deste material ({data_material:%d/%m/%Y}): "
                   "a tabela pode estar desatualizada")]


def situacao_plano(indice: IndiceANS, cd_plano: str | None) -> tuple[PlanoANS | None, list[Achado]]:
    if not cd_plano:
        return None, [Achado("Catálogo ANS", ALERTA, "coluna sem nº de registro ANS: não dá para identificar o produto")]
    candidatos = indice.planos(cd_plano)
    if not candidatos:
        return None, [Achado("Catálogo ANS", ERRO, "registro não existe no catálogo da ANS (erro de leitura ou digitação?)")]
    plano = candidatos[0]
    achados = []
    if plano.situacao == "Suspenso":
        achados.append(Achado("RN 543 art. 12", ALERTA, f"plano com comercialização suspensa desde {_br(plano.dt_situacao)}: não aceita contrato novo"))
    elif plano.situacao != "Ativo":
        achados.append(Achado("Catálogo ANS", ERRO, f"plano {plano.situacao.lower()} desde {_br(plano.dt_situacao)}: não pode ser cotado"))
    operadora = indice.operadora(plano.registro_operadora)
    if operadora and not operadora["ativa"]:
        achados.append(Achado("Cadastro de operadoras", ERRO, f"operadora cancelada em {_br(operadora['data_cancelamento'])} ({operadora['motivo_cancelamento']})"))
    return plano, achados


_ACOMODACAO = {"enfermaria": "Coletiva", "apartamento": "Individual"}


def atributos(plano: PlanoANS, acomodacao: str | None = None, coparticipacao: str | None = None, contratacao: str | None = None) -> list[Achado]:
    """Compara o que o material comercial diz com o registro do produto na ANS."""
    achados = []
    if acomodacao in _ACOMODACAO and plano.acomodacao not in ("", _ACOMODACAO[acomodacao]):
        achados.append(Achado("Atributos × ANS", ALERTA, f"material diz {acomodacao}; ANS registra acomodação '{plano.acomodacao}'"))
    if coparticipacao == "sem" and plano.fator_moderador not in ("Ausente", ""):
        achados.append(Achado("Atributos × ANS", ALERTA, f"material diz sem coparticipação; ANS registra '{plano.fator_moderador}'"))
    if coparticipacao in ("parcial", "total", "com") and plano.fator_moderador == "Ausente":
        achados.append(Achado("Atributos × ANS", ALERTA, "material diz com coparticipação; ANS registra fator moderador ausente"))
    esperado = {"individual_familiar": "Individual", "coletivo_empresarial": "Coletivo empresarial", "coletivo_adesao": "Coletivo por adesão"}
    if contratacao in esperado and not plano.contratacao.startswith(esperado[contratacao]):
        achados.append(Achado("Atributos × ANS", ALERTA, f"material diz {contratacao.replace('_', ' ')}; ANS registra '{plano.contratacao}'"))
    return achados


CARENCIA_MAXIMA_DIAS = {"cpt": 730, "parto": 300, "demais": 180, "urgencia": 1}
TIPOS_DE_CARENCIA = {
    "cpt": re.compile(r"pr[ée]-?existen|\bcpt\b|parcial tempor"),
    "parto": re.compile(r"\bparto"),
    "urgencia": re.compile(r"\burg[êe]ncia|\bemerg[êe]ncia"),
}


def carencia(cobertura: str, dias: int | None) -> list[Achado]:
    if dias is None:
        return []
    texto = cobertura.lower()
    # Palavra inteira ('cirurgia' não é urgência). Texto que cita mais de um tipo fica com o maior limite:
    # a regra acusa o que certamente passa da lei, não o que a redação deixa ambíguo.
    tipos = [t for t, padrao in TIPOS_DE_CARENCIA.items() if padrao.search(texto)] or ["demais"]
    limite = max(CARENCIA_MAXIMA_DIAS[t] for t in tipos)
    if dias > limite:
        return [Achado("Lei 9.656 art. 12 V", ERRO, f"carência de {dias} dias para '{cobertura}' passa do máximo legal ({limite} dias)")]
    return []
