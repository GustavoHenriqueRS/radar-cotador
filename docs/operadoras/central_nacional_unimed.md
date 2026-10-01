# Central Nacional Unimed, Unimed CNU (ANS 339679)

Levantamento de 01/10/2026. Slug: `central_nacional_unimed`. Configuração em `fontes/operadoras/central_nacional_unimed.json`; amostras em `amostras/operadoras/central_nacional_unimed/`.

> **Depois deste levantamento**, o que ele apontou no leitor e no coletor foi corrigido no código, cada caso com teste (`docs/proposta.md`, seção 7):
> - a camada de texto coberta pelo fundo das células sai da leitura: as tabelas DF e Feira de Santana, que davam 0 preços, dão 240 e 280;
> - "Acima 59 anos" passou a ser lido como a última faixa: Salvador dá 100 preços, contra 90 aqui.

É a cooperativa central que opera os planos nacionais do Sistema Unimed para empresas. Não se confunde com as Unimeds singulares (Unimed BH, Unimed Guarulhos etc.), que têm registro próprio. O site mudou de `centralnacionalunimed.com.br` para `unimedcnu.coop.br` (marca "Unimed Nacional").

## Resumo

A CNU tem uma página pública para corretores, o Portal Corretor PME, que lista tabela de preço, manual e portfólio de sete praças. Os PDFs, porém, ficam em `comunicados.centralnacionalunimed.com.br`, cujo robots.txt responde HTTP 504; pela RFC 9309 e pelo `Http` do projeto, isso vale como proibição total, e o robô não baixa nada de lá. Não há cópia dessas tabelas no arquivo da web. O que se alcança são quatro tabelas CNU PME de 2022 e 2023 que a Allcare ainda serve em endereços fixos, todas com produtos suspensos na ANS. Rota recomendada: a captura da página oficial, pronta e desligada até o robots.txt responder, e, enquanto isso, e-mail ou parceria com a CNU.

## Canais verificados

| Canal | Endereço | O que tem | robots.txt / termos | Situação |
|---|---|---|---|---|
| Portal Corretor PME (CNU) | https://unimedcnu.coop.br/web/guest/portal-pme | Links para 24 PDFs em `comunicados.centralnacionalunimed.com.br/site novo/Corretor PME/`: 10 tabelas de preço (PME e linhas Bem e Essencial) de São Paulo, Brasília e entorno, Salvador, Feira de Santana e Santo Antônio de Jesus, Ilhéus e Itabuna, Manaus e São Luís; manual de vendas de 02/2024; portfólio e cronograma 2024 por praça. Também lista as corretoras parceiras por praça e dá acesso ao Portal de Serviços, InovaCom e Conecta+ (login). | `unimedcnu.coop.br` libera tudo. `comunicados.centralnacionalunimed.com.br/robots.txt` respondeu HTTP 504, sem corpo, nas oito tentativas feitas entre 1h e 1h35 de 01/10/2026 (horário de Brasília). | Lista pública; download bloqueado |
| Nossos Planos (CNU) | https://unimedcnu.coop.br/nossos-planos | As quatro linhas nacionais (Ideal, Efetivo, Completo e Único Nacional) com os 12 registros ANS, coparticipação, reembolso e rede em destaque por praça. Sem preço. | Libera. | Público, sem tabela |
| Condições do plano Bem-Estar (flipbook) | https://www.unimed.coop.br/portalunimed/flipbook/cnu/manual_de_vendas/2/ | Link da FAQ do Portal Corretor para as condições gerais de venda. | `www.unimed.coop.br` tem `Disallow: /portalunimed/`. | Bloqueado |
| Domínio antigo | https://www.centralnacionalunimed.com.br | Redireciona para `unimednacional.coop.br` e daí para `unimedcnu.coop.br`. No arquivo da web há só notícias sobre tabela promocional PME e tabela compulsória (2021). | robots.txt 404 (sem restrição). | Sem tabela |
| Arquivo da web | `comunicados.centralnacionalunimed.com.br` | 721 endereços guardados (boletins, imprensa, cartilhas); o último de 17/02/2024. Nada da pasta `site novo/Corretor PME`. | Cópia só serviria com o robots.txt do original permitindo. | Sem cópia |
| Allcare | `corretorallcare.com.br/arquivos/pdf/tabelas/tabela_cnu_pme_{df,salvador_ba,feira_saj_ba,ilheus_itabuna_ba}.pdf` | Quatro tabelas CNU PME (Brasília e Entorno, Salvador, Feira de Santana e Santo Antônio de Jesus, Ilhéus e Itabuna) de 2022 e 2023. A página de materiais da Allcare não lista mais nenhuma tabela CNU; os endereços vieram de buscador e do arquivo da web. | robots.txt libera. | Público, vencido |
| Qualicorp | `tabelasdevendas.qualicorp.com.br/tabelas/QUALIPRO_CNU_SP_F_23.pdf` e `caasp.qualicorp.com.br/QUALIPRO_CNU_FAM_SP_F_22.pdf` (achados por buscador) | Adesão CNU em SP, 2022 e 2023. A Qualicorp vende adesão e PME da CNU (o Plano Personal, no ABC, é anunciado no site da própria Qualicorp como exclusivo dela). | Bucket `tabelasdevendas`: robots.txt responde 403, que o `Http` trata como proibição. `caasp.qualicorp.com.br`: robots.txt 404, PDF no ar (1,3 MB). | Bucket bloqueado; CAASP público, antigo e não baixado |

Pedidos feitos com o `Http` do projeto: 12 em `unimedcnu.coop.br`, 8 na Allcare, 3 no domínio antigo, 3 na CAASP, 1 no site da Qualicorp. Nenhum pedido a `comunicados.centralnacionalunimed.com.br` além do robots.txt.

## Captura configurada

- **Unimed CNU** (fonte nova, `pdf_operadora`):
  - `pagina_publica` no Portal Corretor PME, só as tabelas de preço (`Tabela_de_Precos...pdf`). A descoberta ao vivo funciona e acha as 10 tabelas, mas `Http().permitido` dá falso para todas, porque o robots.txt do host dos PDFs não responde. Ficou **desligada**; deve ser ligada quando esse robots.txt responder 200 com permissão ou 404. Os nomes não têm data: a CNU troca o arquivo no lugar, e o download condicional (ETag, Last-Modified) e o hash pegam a troca.
  - `caixa_email`, modelo desligado, com remetentes `@unimedcnu.coop.br` e `@unimednacional.coop.br` (domínios dos e-mails publicados em https://unimedcnu.coop.br/novos-produtos).
- **Allcare** (fonte existente, só a captura nova): `url_direta` com as quatro tabelas CNU PME, **desligada**. Os endereços estão no ar e o robots.txt permite, mas o material é de 2022 e 2023 e todos os produtos estão suspensos. Serve para teste e histórico, não para preço vigente.
- **Não configurado**: a Qualicorp (bucket bloqueado; a tabela da CAASP é de 2022) e o flipbook (bloqueado no robots.txt).

## Amostras e leitura

As três amostras são as tabelas da Allcare; as tabelas atuais do portal não puderam ser baixadas. Leitura geométrica, sem LLM, com o código do leitor de 01/10/2026 01h38 (ele mudou durante o levantamento; a rodada anterior deu os mesmos números, sem o alerta de documento nas tabelas de 2022).

| Arquivo | Conteúdo | Preços | Colunas com registro | Revisão | Erros / alertas |
|---|---|---|---|---|---|
| `allcare_cnu_pme_df_2022-05.pdf` | Brasília e Entorno, "Tabela de preços, Maio 2022"; 12 registros | 0 | 0 | 0 | 0 / 1 |
| `allcare_cnu_pme_ba_salvador_2023-06.pdf` | Salvador, "Tabela de Preços, Junho 2023"; 5 produtos nacionais em livre adesão e contratação compulsória | 90 | 10 de 10 | 90 | 0 / 20 |
| `allcare_cnu_pme_ba_feira_saj_2022-05.pdf` | Feira de Santana e Santo Antônio de Jesus, "Maio 2022"; 14 registros | 0 | 0 | 0 | 0 / 1 |

Em Salvador, os 90 valores lidos batem com o PDF: 84 confirmados pelo cálculo do padrão de faixas e 6 só pela leitura geométrica, porque o valor recalculado difere em 2 ou 3 centavos. O leitor aponta certo os cinco produtos como suspensos desde 13/06/2024 ("não aceita contrato novo"). Os 16 registros distintos das três tabelas estão todos suspensos na ANS (14 desde 13/06/2024, 2 desde 28/09/2022).

Problemas do leitor:

1. **Texto sobreposto, nenhum preço lido.** Em `allcare_cnu_pme_df_2022-05.pdf` e `allcare_cnu_pme_ba_feira_saj_2022-05.pdf`, p. 5 a 8, cada preço tem duas ou três camadas de texto: o valor visível, em UnimedSans-Book 8,5 pt, e um valor antigo escondido, em UnimedSans-Regular 9,0 pt, 1,7 pt acima. O `extract_words` de `ler_paginas` (`leitor/pdf.py`) junta os caracteres das camadas numa só palavra ("RR$$ 224103,,4881" é R$ 240,48 intercalado com R$ 213,81), e `_descartar_invisiveis` decide por palavra, então não separa as camadas. Resultado: 0 preços nas duas tabelas; o leitor só avisa, no documento, que não achou tabela por faixa etária. Separar as palavras por fonte e tamanho (`extra_attrs=["fontname", "size"]`) antes do filtro, ou cair para OCR quando o texto vier duplicado, deve resolver.
2. **Faixa "Acima 59 anos" não reconhecida.** Em `allcare_cnu_pme_ba_salvador_2023-06.pdf`, p. 6 e 7, a última faixa vem como "Acima 59 anos", sem "de". O `_RE_FAIXA` de `leitor/faixas.py` aceita "acima de 59", mas não essa forma; as 10 colunas ficam sem a faixa 59+ (90 de 100 preços), e cada uma recebe o alerta "faixas não lidas: 59+".

## Na ANS

Índice local, pda-008 de 30/09/2026. UNIMED CNU - COOPERATIVA CENTRAL, CNPJ 02.812.468/0001-06, cooperativa médica, sede em SP, ativa.

| Situação | Total | Coletivo empresarial | Coletivo por adesão | Individual ou familiar | Empresarial + adesão |
|---|---|---|---|---|---|
| Ativo | 497 | 476 | 18 | 3 | 0 |
| Suspenso | 829 | 394 | 245 | 190 | 0 |
| Cancelado | 686 | 449 | 133 | 88 | 16 |
| Transferido | 2 | 1 | 0 | 1 | 0 |
| Total | 2.014 | 1.320 | 396 | 282 | 16 |

- Ativos com nota técnica de preço: 372. Dos 125 sem nota, 113 são ambulatorial e hospitalar com obstetrícia; 46 foram registrados em 2026 e 19 em 2025.
- Ativos registrados em 2026: 106; em 2025: 96; em 2024: 101. Por abrangência: nacional 417, grupo de municípios 67, municipal 12, estadual 1. Por fator moderador: coparticipação 375, sem 121, franquia 1.
- Os 12 registros das linhas anunciadas em "Nossos Planos" (Ideal, Efetivo, Completo e Único Nacional PJ) estão ativos desde agosto de 2025, coletivo empresarial, abrangência nacional, com nota técnica.
- A adesão ativa é pequena: 18 planos, entre eles Unimed Básico, Especial e Master ADS I (março a maio de 2026) e Ideal Nacional ADS I, registrado em 22/09/2026. No individual, só 3 planos Ideal Regional PF I (julho de 2026).

## Lacunas e próximo passo

1. **robots.txt de `comunicados.centralnacionalunimed.com.br`**: acompanhar. Se passar a responder (200 com permissão ou 404), ligar a captura da página. Se continuar em 504, pedir à CNU, pelo canal de corretores, envio por e-mail ou outro endereço para o material.
2. **Vigência do material do portal**: o cronograma é de 2024 e o manual de 02/2024; sem baixar as tabelas não dá para saber se trazem o portfólio novo (registros de 2025) ou produtos já suspensos.
3. **Adesão**: a parceira é a Qualicorp, cujo bucket de tabelas é bloqueado pelo robots.txt. Não há tabela de adesão CNU atual alcançável; a da CAASP é de 2022.
4. **Leitor**: os dois problemas acima (camadas de texto sobrepostas e "Acima 59 anos") precisam de correção no código central.
5. **Não verifiquei**: o conteúdo das tabelas atuais do portal; a tabela da Allcare de Ilhéus e Itabuna (não baixada, limite de três amostras); a tabela da CAASP.
