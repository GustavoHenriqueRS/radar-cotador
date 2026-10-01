# Saúde Sim (ANS 320111)

Levantamento de 01/10/2026. Slug: `saude_sim`.

> **OPERADORA EXTINTA.**
>
> - O registro 320111 é da MASSA FALIDA DE SAÚDE SIM LTDA (CNPJ 02.464.179/0001-63), Brasília/DF.
> - A ANS cancelou o registro em 10/08/2022 por liquidação extrajudicial, e os 117 planos estão cancelados.
> - O TJDFT decretou a falência em junho de 2023.
> - Não há material de venda a capturar. Qualquer tabela, cotação ou anúncio da Saúde Sim hoje é divergência a apontar, e a cotação deve ser bloqueada.

## Resumo

O nome confere com o registro: o nome fantasia na ANS é "SAÚDE SIM", com sede em Águas Claras/DF. O que não confere é a situação: a operadora não existe mais.

- 08/08/2022: a ANS concedeu portabilidade especial de carências aos beneficiários pela Resolução Operacional nº 2.757, com prazo de até 60 dias.
- 10/08/2022: o registro foi cancelado.
- 06/2023: o TJDFT decretou a falência (processo 0701236-26.2023.8.07.0015).

O antigo site (`saudesim.med.br`) nem resolve mais no DNS. Mesmo assim, a página do Cotador citava a Saúde Sim entre as operadoras atendidas (`docs/pesquisa/fontes-e-achados.md`, seção 1), e resultados de busca ainda mostram corretoras oferecendo "cotação" de plano Saúde Sim. Rota recomendada: nenhuma captura. A fonte fica registrada só para o radar mostrar o motivo do bloqueio.

## Canais verificados

| Canal | Endereço | O que tem | robots.txt / termos | Situação |
|---|---|---|---|---|
| Cadastro da ANS (local) | `dados/ans/Relatorio_cadop_canceladas.csv` | Registro 320111, cancelado em 10/08/2022, motivo "Liquidação Extrajudicial". Não consta em `Relatorio_cadop.csv` (ativas). | Dado aberto | Fonte de verdade |
| Resolução da ANS | https://bvsms.saude.gov.br/bvs/saudelegis/ans/2022/res2757_10_08_2022.html | RO 2.757/2022: portabilidade especial de carências, até 60 dias | Permite (`Disallow: /wp-admin/`) | Verificado |
| Notícia do TJDFT | https://www.tjdft.jus.br/institucional/imprensa/noticias/2023/junho/tjdft-decreta-falencia-de-operadora-de-plano-de-assistencia-a-saude | Falência decretada (notícia de 12/06/2023) | Permite | Verificado |
| Notícia da ANS | https://www.gov.br/ans/pt-br/assuntos/noticias/beneficiario/ans-concede-beneficio-para-clientes-da-operadora-saude-sim | A página mostra "Conteúdo restrito" e pede login | Permite | Não acessado além disso |
| Site antigo | https://www.saudesim.med.br/ (domínio do e-mail no cadastro da ANS) | O domínio não resolve no DNS | Sem robots.txt alcançável. O `Http` do projeto trata isso como proibido. | Morto |
| Arquivo da web | API CDX, domínio saudesim.med.br | 118 PDFs guardados entre 2016 e 2021. Detalhe abaixo da tabela. | O robots.txt do original não responde, e o motor bloqueia a cópia (`backend/radar/coleta.py`, conferência do `url_original`) | Não coletável |
| Corretoras que ainda anunciam | planodesaudesim.com.br, planodesaudebrasiliadf.com.br/saudesim-brasilia/, healthcarebrasilia.com, gruposaudebrasil.com | Títulos como "Saúde Sim Brasília – cotação na hora" e "SaúdeSim Brasília com 50% desconto" nos resultados de busca | Não acessados | Divergência de mercado |

O que o arquivo da web guarda do site antigo:

- listas de rede por linha (SIM Certo, SIM Clássico, SIM Essencial, SIM Exato, SIM Exclusivo, SIM Mais, Super SIM I e II);
- comunicados de descredenciamento e de resilição de prestadores;
- manual do beneficiário;
- um comunicado de reajuste por agrupamento de 2018.

Nenhum desses PDFs é tabela de preço. A última cópia é de 24/09/2021.

Não há canal restrito a mencionar: a operadora não opera.

## Captura configurada

Arquivo: `fontes/operadoras/saude_sim.json`.

- Fonte **Saúde Sim** (`site_operadora`, confiabilidade 1, sem capturas). As observações dizem que a operadora está extinta e que a cotação deve ser bloqueada.
- **Sem `caixa_email` de modelo.** Uma operadora extinta não manda material ao corretor, e um e-mail com o nome dela seria sinal de fraude ou de material velho, não de tabela.
- **Sem `wayback`.**
  - Não há tabela de preço no histórico.
  - O motor bloquearia a captura de qualquer forma: com o domínio original fora do ar, `Http.permitido()` devolve falso, e `coleta.py` exige que o robots.txt do original permita a cópia arquivada.
  - Para operadoras extintas, essa regra conservadora impede reconstruir o histórico pelo arquivo da web. É uma escolha de projeto a registrar, não um erro.
- `python -m coletor.fontes` valida sem problemas.

## Amostras e leitura

Nenhuma amostra.

- Não existe tabela de venda pública vigente.
- O único histórico (arquivo da web) não tem tabela de preço.
- O robots.txt do domínio original não pode ser conferido, e pela regra do projeto isso conta como proibido.

O leitor não foi executado.

## Na ANS

Índice local `dados/ans/indice.sqlite` (pda-008 de 30/09/2026) e CADOP.

- Operadora cancelada: registrada em 27/01/1999, cancelada em 10/08/2022, motivo "Liquidação Extrajudicial".
- 117 planos, todos cancelados. Nenhum ativo e nenhum suspenso.

| Contratação | Cancelado |
|---|---|
| Coletivo empresarial | 54 |
| Coletivo por adesão | 47 |
| Individual ou familiar | 15 |
| Coletivo empresarial + coletivo por adesão | 1 |

- **Datas dos cancelamentos:**
  - 68 planos cancelados em 10/08/2022, no mesmo dia do registro: 34 empresariais, 23 de adesão e 11 individuais;
  - 44 em 2019;
  - 5 em 2006 e 2009.
- Nenhum plano tem nota técnica de preço (VCM) no índice local.
- No cadastro da ANS não há outra operadora ativa com "Saúde Sim" no nome, nem outro registro com o mesmo CNPJ. Não existe sucessora com a marca.

## Lacunas e próximo passo

- **Bloqueio no cotador.**
  - O radar deve listar "Saúde Sim" como operadora cancelada em qualquer tela de cobertura (o README já menciona isso no Painel).
  - Deve recusar documento novo que cite o registro 320111 ou os produtos dele.
  - Qualquer tabela recebida por e-mail ou upload com essa marca deve virar alerta, não preço.
- **Não verifiquei:**
  - se os sites de corretora dos resultados de busca ainda estão no ar e oferecendo o plano; não os acessei, por serem agregadores ou captação de contato;
  - o texto completo da notícia da ANS no gov.br, que hoje pede login.
- **Próximo passo:** decidir se operadora extinta merece exceção na regra do robots.txt para o arquivo da web, só para auditoria. A sugestão é não abrir a exceção: o cadastro da ANS já basta para o bloqueio.
