# SulAmérica Saúde (ANS 006246)

Levantamento de 01/10/2026. Slug: `sulamerica_saude`.

> **Depois deste levantamento**, o que ele apontou no leitor e no coletor foi corrigido no código, cada caso com teste (`docs/proposta.md`, seção 7):
> - a conferência passou a usar a nota técnica plausível para a data do material. A tabela de 10/2023 deixou de ter os alertas falsos de "abaixo da despesa" (eram 112, agora nenhum). Sobram os 12 erros reais de plano cancelado, e 144 colunas avisam que a operadora registrou nota técnica nova depois do material;
> - material sem grade de preço (tabelas de coparticipação) passou a gerar aviso.

## Resumo

A SulAmérica não publica tabela de preço. O portal (portal.sulamericaseguros.com.br) e o site sulamerica.com.br, com robots.txt que libera as pastas de saúde, publicam condições gerais, exemplos de reembolso e tabelas de coparticipação com limite por evento, trocadas no mesmo endereço (PME I e PME Mais em maio de 2026, Adesão em junho de 2026). O preço de adesão sai pela Qualicorp, mas o `tabelasdevendas` responde 403 ao pedido de robots.txt e fica bloqueado; a única tabela de preço baixável é uma versão de OUT/2023 num subdomínio da Qualicorp sem restrição. Rota recomendada: página pública e endereço fixo para condições; caixa de e-mail e parceria com a Qualicorp para preço.

## Canais verificados

| Canal | Endereço | O que tem | robots.txt / termos | Situação |
|---|---|---|---|---|
| Portal, planos nacionais (PME 3 a 29) | https://portal.sulamericaseguros.com.br/para-empresa/saude/planos-nacionais/ | Links diretos para 3 condições gerais, 4 tabelas de coparticipação PME (três no próprio portal, atualizadas entre 13/05/2025 e 02/12/2025, e a PME I, em sulamerica.com.br), 2 exemplos de reembolso e o plano referência | Só linhas comentadas (`#User-Agent:*`, `#Disallow: /v2(.*)$`): nada vedado. Termos: o conteúdo é da SulAmérica; sem cláusula sobre robôs | Captura ativa |
| Portal, PME Mais (30 a 99) | https://portal.sulamericaseguros.com.br/para-empresa/saude/planos-nacionais/sulamerica-saude-pme-mais-30-a-99-pessoas/ | 2 condições gerais, plano referência, 2 exemplos de reembolso | Idem | Captura ativa |
| Portal, PME 3 a 29 (nova) e Adesão | .../sulamerica-saude-pme-03-a-29-pessoas/ e .../para-empresa/saude/sulamerica-saude-adesao/ | Aplicação Angular; o HTML não traz links | Idem | Sem captura |
| Portal, central de documentos | https://portal.sulamericaseguros.com.br/central-de-documentos | Contratos e manuais, montados por JavaScript | Idem | Não explorado |
| sulamerica.com.br, endereços fixos | https://www.sulamerica.com.br/saude/ | Tabelas de coparticipação PME I (Last-Modified 14/05/2026), PME Mais (13/05/2026), Adesão I e Adesão (01/06/2026), PME (15/05/2025); exemplos de reembolso (31/07/2025); folhetos de apoio às vendas PME (27/12/2023) e PME Mais (06/10/2022) | `Disallow` só em `/convite/`, `/cp/`, `/emkt/`, `/relatorioanual2007/`; `Allow: /` | Captura ativa |
| Saúde Cotador | https://os11.sulamerica.com.br/SaudeCotador/ | Cotação PME do corretor (o manual de 2016 é público em `/saude/manual_cotador_completo.pdf`) | Login | Restrito, não acessado |
| Arquivo da web | CDX de `www.sulamerica.com.br/saude/` | 14 cópias de tabelas de coparticipação e folhetos desde 2023, com conteúdo diferente entre versões | Permite | Captura inativa |
| Qualicorp (tabelasdevendas) | https://tabelasdevendas.qualicorp.com.br/tabelas/QUALIPRO_SAS_* | Manuais QualiPRO de adesão SP (2023 a 2025, com anexos `AN_001` e `AN_002` e a linha hospitalar 506), segundo os títulos no buscador | `/robots.txt` responde HTTP 403; o `Http` do projeto trata como proibido | Bloqueado |
| Qualicorp (subdomínio da CAASP) | https://caasp.qualicorp.com.br/QUALIPRO_SAS_SP_F_23_NP.pdf | Manual QualiPRO SulAmérica SP de OUT/2023, validade setembro/2023 a agosto/2024 | `/robots.txt` responde 404: sem restrição | Captura ativa (histórico) |
| Qualicorp (página de captação) | https://escolha.qualicorp.com.br/sulamerica/ | Formulário de cotação, sem PDF | `/robots.txt` responde 404 | Sem captura |
| Aliança Administradora | https://aliancaadm.com.br/planos-de-saude/ | Lista a SulAmérica (006246); preço só pelo simulador | `Disallow: /wp-admin/` | Sem PDF público |
| Supermed | https://vendas.supermed.com.br/ | Portal de vendas da administradora | `/robots.txt` responde HTTP 403 | Bloqueado, não acessado |
| sulamericasaudeonline.com.br | `/est_saudeonline/empresa/pdf/TabelaEmpresarialPME.pdf` e outros | Tabela de reembolso e lista de produtos antigas | HTTPS com certificado vencido (o `Http` trata como bloqueio); HTTP com robots 404 | Não usado: legado, dono do domínio não confirmado |
| Corretora DWS | https://dwscorretora.com/apoio-ao-corretor/sulamerica/ | Cópias de folhetos, lâminas e condições gerais de 2022 e 2023 | `Disallow: /wp-admin/` | Descartado: cópia de terceiro e defasada |
| Corretoras e comparadores | Vários ("tabela SulAmérica 2026") | Preços compilados de várias operadoras | — | Descartados (regra 4) |

## Captura configurada

Arquivo `fontes/operadoras/sulamerica_saude.json`.

Fonte "SulAmérica Saúde" (`site_operadora`, confiabilidade 5):

| Captura | Tipo | Ativa | Teste ao vivo | Por quê |
|---|---|---|---|---|
| Documentos do PME (3 a 29 vidas) | `pagina_publica` | sim | 10 candidatos | Condições gerais, coparticipação, reembolso e plano referência linkados na página |
| Documentos do PME Mais (30 a 99 vidas) | `pagina_publica` | sim | 5 candidatos | Idem para o PME Mais |
| Tabelas de coparticipação e reembolso em endereço fixo | `url_direta` | sim | 6 candidatos | A SulAmérica troca o arquivo no mesmo endereço. Cobre PME Mais e Adesão, que nenhuma página estática linka |
| Folhetos de apoio às vendas | `url_direta` | sim | 2 candidatos | Material de apoio à venda do PME e do PME Mais (características, contratação, carências, segundo a descrição no buscador; não abri os PDFs) |
| Histórico das tabelas de coparticipação e folhetos | `wayback` | não | 14 candidatos | Ligar uma vez para montar o histórico; com `somente_series_conhecidas`, só as séries acima |
| Tabelas enviadas ao corretor | `caixa_email` | não | não testada (modelo) | Canal de preço. Remetente `@sulamerica.com.br` |

Fonte "Qualicorp" (mesmo nome e tipo do arquivo raiz; o arquivo só acrescenta capturas):

| Captura | Tipo | Ativa | Teste ao vivo | Por quê |
|---|---|---|---|---|
| SulAmérica adesão SP na página da CAASP | `url_direta` | sim | 1 candidato | Única tabela de preço da SulAmérica em endereço que o robots.txt permite. Versão vencida, que serve de histórico da série `QUALIPRO_SAS_SP_F` |
| SulAmérica adesão SP em tabelasdevendas | `url_direta` | não | 3 candidatos | Endereços achados por buscador e não verificados: o robots.txt responde 403. Ficam prontos para uma autorização da Qualicorp |

- Filtro das páginas: `incluir` `(?i)(coparticipa|reembolso|_CG(_|%20)|plano_referencia)[^/]*\.pdf$` e `excluir` `(?i)/vida/|viagem|odonto`. Ficam de fora guias de leitura contratual, a lista de produtos de 2015, informações financeiras, seguro viagem e vida.
- A página de PME e a `url_direta` trazem os mesmos dois arquivos (PME I e exemplos de reembolso), em `http`/`https` e com ou sem `www`. A chave de série ignora essas diferenças, então caem na mesma série. A duplicação é de propósito: as páginas de PME 3 a 29 e de Adesão já viraram aplicação Angular sem links no HTML, e a de planos nacionais pode ir pelo mesmo caminho.
- O domínio de e-mail tem MX e DMARC `p=reject` no DNS. Um folheto de sucursal da própria SulAmérica (`sulamerica.com.br/nac/pdfs/Folheto_Curitiba.pdf`, visto pelo buscador) lista a equipe em `@grupo.sulamerica.com.br`. O filtro `@sulamerica.com.br` cobre o domínio e os subdomínios.

## Amostras e leitura

Pasta `amostras/operadoras/sulamerica_saude/`, com `manifest.json`. Leitura geométrica, sem LLM.

| Arquivo | O que é | Páginas | Preços lidos | Colunas com registro ANS | Para revisar | Erros / alertas |
|---|---|---|---|---|---|---|
| `sulamerica_coparticipacao_pme_mais_2026-05-13.pdf` | Coparticipação PME Mais, contratos a partir de 14/05/2026 | 75 | 0 | 0 | 0 | 0 / 0 |
| `sulamerica_coparticipacao_adesao_i_2026-06-01.pdf` | Coparticipação Adesão I, vigência a partir de julho/2023 | 75 | 0 | 0 | 0 | 0 / 0 |
| `qualicorp_caasp_sulamerica_adesao_sp_2023-11.pdf` | QualiPRO SulAmérica SP, OUT/2023 | 49 | 1.560 | 156 de 156 (24 registros, todos do 006246) | 340 | 12 / 123 |

A tabela da Qualicorp foi lida em 10 s. 1.546 preços foram confirmados pelo padrão de faixas. Os outros 14 ficam só na leitura geométrica, a R$ 0,02 do cálculo (arredondamento). Conferi os 1.546 valores escolhidos contra o texto das páginas 20 a 29, e todos aparecem. A condição de cada grade saiu certa: composição (titular, + 1, + 2 ou mais), região (capital, interior 1, interior 2) e coparticipação. Os 340 itens para revisão vêm todos de regra, nenhum de leitura:

- 120 vêm de 12 colunas de 4 planos cancelados na ANS em 29/07/2025, depois da tabela: 495.665/23-6 e 495.667/23-2 na p21, 495.669/23-9 e 495.670/23-2 na p23. Esses são os 12 erros.
- 112 vêm de alerta RN 564 art. 5º (preço abaixo da despesa assistencial da nota).
- 108 vêm de alerta RN 564 art. 6º §2º (fora da banda de ±30%).

Problemas do leitor:

1. **A conferência usa a nota técnica mais recente, não a da data da tabela (código central).** `leitor/conferencia.py:227` chama `indice.notas_vigentes(...)` (`leitor/ans.py:182`), que sempre devolve a nota mais recente do plano. Além disso, `leitor/regras.py:118` mede a idade da nota contra a data de hoje. Na tabela de OUT/2023, os 112 alertas art. 5º comparam preço de 2023 com notas de 28/03/2024 (99), 25/08/2026 (11) e 26/06/2024 (2). Os planos têm nota de 25/10/2023 no índice. Repeti a regra (`regras.referencia_ntrp`) com a nota mais recente até 31/10/2023 e com essa data como "hoje": ficariam 39 alertas art. 5º e 26 art. 6º §2º, em vez de 112 e 11. Sem LLM, o leitor nem extrai a vigência (só a leitura por LLM preenche `vigencia_inicio`). Mesmo com ela, a conferência não a usa para escolher a nota. O problema vale para toda tabela antiga: versões do Wayback e anteriores.
2. **Rótulo de coluna com texto do painel lateral.** Nas páginas 24 a 29, 75 de 132 rótulos levam pedaços como "PLANOS reajuste:", "em Reais (R$), per" ou "o Beneficiário.". O registro e a condição não são afetados. Nas versões 2024-11 e 2026-06 da mesma série, lidas com LLM no acervo, os rótulos vêm limpos.
3. **Tabela de coparticipação passa em branco.** As duas tabelas de coparticipação dão 0 preço, o que é certo, mas sem achado de documento. O que interessa ao cotador está em duas páginas que o leitor não extrai:
   - página 3: limite por evento, 30%, em 7 grupos de evento × 6 ou 7 colunas de linha. Na PME Mais, a consulta vai de R$ 36,61 (Direto) a R$ 207,45 (Prestige);
   - página 75: produtos com registro ANS. Conferi essa página à parte: os 30 registros da PME Mais estão ativos; dos 57 da Adesão I, 5 estão cancelados na ANS (4 em 29/07/2025 e 1 em 07/08/2023). Na PME Mais o registro vem sem máscara (`495510232`).

## Na ANS

Índice local (`dados/ans/indice.sqlite`, PDA atualizado em 30/09/2026). Sul America Companhia de Seguro Saúde, CNPJ 01.685.053/0001-56, seguradora especializada em saúde, ativa.

| Situação | Coletivo empresarial | Coletivo por adesão | Individual ou familiar | Total |
|---|---|---|---|---|
| Ativo | 554 | 270 | 0 | 824 |
| Suspenso | 347 | 116 | 290 | 753 |
| Cancelado | 346 | 90 | 69 | 505 |
| Transferido | 817 | 28 | 0 | 845 |
| Total | 2.064 | 504 | 359 | 2.927 |

- Ativos: 596 de abrangência nacional, 203 por grupo de municípios e 25 estaduais; 432 com coparticipação e 392 sem. Destes, 62 são odontológicos registrados no mesmo número, e são exatamente os 62 ativos sem nota técnica. Os outros 762 têm nota; a mais recente é de 25/08/2026.
- Em 2026:
  - 12 planos registrados (11 empresariais e 1 de adesão);
  - 131 suspensões: 11 individuais em março, 89 empresariais em maio e 31 em julho. As de maio pegam linhas antigas (Acesso, Pequena Empresa, Estilo, Diamante, Prata, Supremo, Absoluto);
  - 54 cancelamentos.
- Outros registros do grupo:
  - 416428 SulAmérica Paraná Clínicas Serviços de Saúde (CNPJ 02.866.602/0001-51, medicina de grupo): 742 ativos (733 empresariais, 8 de adesão, 1 individual), com 141 registrados em 2026 contra 12 no 006246. Há produtos PME com os mesmos nomes de linha (Direto, Exato, Especial 100, Executivo) nos dois números;
  - 417815 SulAmérica Odontológico: 110 ativos.

  O radar precisa acompanhar ao menos 006246 e 416428.

## Lacunas e próximo passo

- Preço vigente: só pela Qualicorp (`tabelasdevendas`, bloqueado pelo robots 403) ou pelo Saúde Cotador (login). Próximos passos:
  - pedir à Qualicorp autorização expressa, ou um robots.txt que libere `/tabelas/`, e ativar a captura que já está configurada;
  - montar a caixa de e-mail para o material do comercial da SulAmérica.
- Portal em migração: se a página de planos nacionais virar aplicação Angular como as de PME e Adesão, as duas capturas por página zeram. As `url_direta` cobrem as tabelas de coparticipação, mas as condições gerais (endereços `data/files/…` que mudam a cada versão) ficam sem descoberta.
- Leitor (código central):
  - escolher a nota técnica pela data da tabela e medir a idade da nota contra essa data;
  - extrair a grade de limites de coparticipação e a lista de registros das tabelas de coparticipação.
- Não verifiquei:
  - o Saúde Cotador e a central de documentos (aplicação, API não procurada);
  - se `caasp.qualicorp.com.br` tem versões mais novas: não há listagem, e não testei nomes de arquivo;
  - os três endereços de `tabelasdevendas`;
  - o dono de `sulamericasaudeonline.com.br`;
  - a página do empresarial acima de 100 vidas, que não consultei.
