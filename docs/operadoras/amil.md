# Amil (ANS 326305)

Levantamento de 01/10/2026. Slug: `amil`.

> **Depois deste levantamento**, o que ele apontou no leitor e no coletor foi corrigido no código, cada caso com teste (`docs/proposta.md`, seção 7):
> - o rótulo "59" com o "ou +" na linha de baixo passou a ser lido: a Linha Especial dá 360 de 360 preços, contra 324 aqui.

## Resumo

O único canal público oficial é o Kit Corretor (kitcorretoramil.com.br), mantido pela própria Amil. Em PDF fixo ele oferece o Manual de Vendas PME, que traz as condições (coparticipação, reembolso, reajuste por faixa, carências) mas nenhum preço, e algumas tabelas avulsas antigas. O preço vigente de PME, PJ e adesão é montado na tela por chamadas POST, e o PDF de preço é gerado na hora, sem endereço fixo. Os termos de uso da Amil vedam aplicações automatizadas; o site institucional e a Qualicorp bloqueiam robôs. Rota recomendada: autorização ou parceria com a Amil para ler o Kit, e enquanto isso a caixa de e-mail que recebe os comunicados ou o upload do PDF que o corretor gera no Kit. Todas as capturas ficaram configuradas e inativas.

**Divergência a apontar no radar**

- **A tabela "Ana Costa" do Kit Corretor não é da 326305.** O Kit publica em `pdfs/operadora-regional/ana-costa.pdf` uma tabela da Plano de Saúde Ana Costa Ltda. (ANS 360244), operadora do grupo Amil cancelada em 10/06/2026 por incorporação.
  - Os registros da tabela (479.257/17-2, 479.264/17-5 e 402.252/99-1) aparecem como "Transferido" na 360244 e, desde 09/09/2026, como "Suspenso" na Santa Helena Assistência Médica S/A. (355097).
  - Essa tabela fez parte do acervo de teste no começo do projeto. Saiu dele pelo mesmo motivo das outras amostras do Kit: os termos de uso da Amil.

## Canais verificados

| Canal | Endereço | O que tem | robots.txt / termos | Situação |
|---|---|---|---|---|
| Kit Corretor Amil (operadora) | https://kitcorretoramil.com.br/ | Rodapé: "Amil Assistência Médica Internacional S/A, CNPJ 29.309.127/0001-79", o mesmo da 326305. Em PDF fixo: Manual de Vendas PME (`pdfs/Manual_de_Vendas_PME.pdf?updated=16-09-2026`), manuais Dental e Regionalizadas, 18 "Modelo PDF online" de adesão e tabelas avulsas antigas em `wp-content/uploads/`. | Só `Disallow: /wp-content/themes/kitcorretor/bkp`. O rodapé não traz termos próprios. Os termos da Amil vedam aplicações automatizadas (ver abaixo). | Público, sem login. Capturas configuradas e inativas |
| Kit: tabela de preço na tela | `/linha-amil-pj/tabela-de-precos-pj/`, `/linha-selecionada-pme/tabela-de-precos-pme/`, `/contrato-coletivo-por-adesao/tabela-de-precos/` | Preço por estado, porte e coparticipação, carregado do `app.js` por POST em `admin-ajax.php?action=ktc_get_price_table_values` (PME e PJ) e em `/wp-json/adesao/query` (adesão) | robots.txt permite | Público, mas só por POST: nenhum tipo de captura do projeto faz POST. Não usado |
| Kit: gerador de PDF | https://pdf.kitcorretoramil.com.br/pdf | Recebe por POST o HTML da tabela do estado e devolve o endereço de um PDF gerado na hora | robots.txt responde 404 | Não usado (POST, endereço muda a cada pedido) |
| Kit: "Modelo PDF online" de adesão | 18 links na página de adesão (17 médicos e 1 dental), ex.: `wp-content/uploads/2026/09/Modelo_PDF_ONLINE_TABELA__Prata_SP_II_1.pdf` | Abri só o de Prata II SP (5 páginas em imagem, Last-Modified 28/09/2026, "ANS nº 326305" no rodapé). Apesar do nome, traz só a área de comercialização (lista de municípios), sem preço. Descartei; os outros 17 não abri | robots.txt permite | Público; o que abri não tem preço |
| Kit: tabela avulsa | `wp-content/uploads/2025/03/Linha-Especial-Amil-6.pdf` | Tabela de preço da Linha Especial (RJ), de março de 2025. Achada por buscador; não está ligada nas páginas atuais | robots.txt permite | Público, antiga. Baixada como amostra |
| Site institucional | https://www.amil.com.br/ | — | robots.txt responde 403: o cliente HTTP do projeto trata como bloqueio total | Não acessado |
| Institucional (termos e lista de produtos) | https://institucional.amil.com.br/ | Termos de uso e lista oficial de planos ativos (PDF de set/2026, segundo a pesquisa do projeto) | robots.txt permite essas páginas, mas o servidor devolve 403 ao agente identificado (WAF) | Bloqueado; não contornei |
| Plataforma Comercial e vendas.amil.com.br | https://vendas.amil.com.br/login | Cotação com o preço final, que o manual manda usar | Login | Restrito |
| Allcare: arquivo fora da página | https://www.corretorallcare.com.br/arquivos/pdf/tabelas/tabela_amil_df_a.pdf | Adesão DF, modelo Allcare, de junho de 2023. A página de materiais não lista mais a Amil | robots.txt permite | No ar, sem link; produtos suspensos. Baixada como amostra |
| Qualicorp | https://tabelasdevendas.qualicorp.com.br/ | Tabelas de adesão; o buscador mostra tabelas com a Amil | robots.txt responde 403 | Não acessado |
| Supermed (administradora da adesão Amil) | https://www.supermed.com.br/nossos-planos/amil | Página institucional, sem tabela. O material do corretor fica em vendas.supermed.com.br (login) e no app | `Allow: /` | Sem material público |
| Arquivo da web | API CDX do web.archive.org | 91 cópias de PDFs do Kit desde 2023: manuais e normativas PME da Amil (2023, 2024 e 4 versões distintas do manual atual, de 20/07/2025 a 15/04/2026), tabelas das operadoras regionais e folhetos. Pelo nome, nenhum é tabela de preço da 326305 (não abri) | O robots.txt do arquivo responde 404; o do Kit permite o original | Captura configurada, inativa |
| E-mail | amilofertascorretor@amil.com.br, impresso na tabela Linha Especial | Canal de proposta da Linha Especial | — | Modelo de caixa inativo com `@amil.com.br` |

Termos de uso: a página `institucional.amil.com.br/termos-de-uso-e-condicoes-de-navegacao` devolveu 403 ao robô identificado. Li o trecho pelo buscador: o portal foi feito para uso humano, e aplicações automatizadas e mineração de dados são vedadas. Não consegui verificar se o "portal Amil" dos termos inclui o domínio do Kit.

Não usados: sites de corretoras e comparadores com "tabela Amil 2026" em HTML (lifebis, fortplanos, amilsaudebr, planoamilempresas e outros), porque não são canal oficial ou compilam várias operadoras.

Pedidos feitos: 28 ao Kit (somando as leituras de robots.txt), 14 à Allcare, 13 ao arquivo da web e 7 à Supermed.

## Captura configurada

Arquivo: `fontes/operadoras/amil.json`.

- **Amil (Kit Corretor)**, fonte nova (`pdf_operadora`, confiabilidade 5):
  - `pagina_publica`, **inativa**. Lê a página inicial do Kit e pega só o Manual de Vendas PME. Descoberta ao vivo: 1 candidato. A data da versão vem na query (`?updated=16-09-2026`), e o padrão de data só olha o caminho, então a versão fica sem data. A série continua estável, porque a chave ignora a query.
  - `wayback`, **inativa**. Prefixo `.../kitcorretor/pdfs/` filtrado no manual. Descoberta ao vivo: 4 versões distintas (20/07/2025, 14/11/2025, 20/12/2025 e 15/04/2026).
  - `url_direta`, **inativa**, para a tabela Linha Especial de março de 2025. É material avulso, sem link nas páginas, e não serve como "tabela vigente".
  - `caixa_email`, **inativa** (modelo): servidor e usuário de exemplo, senha em `COLETA_EMAIL_SENHA`, remetente `@amil.com.br`.
- **Allcare** (mesmo nome e tipo da fonte existente): `url_direta` **inativa** para a tabela Amil DF de 2023, fora da página de materiais. Fica como registro e caso de teste do radar, não como coleta periódica.

Por que tudo inativo: o robots.txt do Kit permite e a descoberta funciona, mas os termos da Amil vedam acesso automatizado. A pesquisa (`docs/pesquisa/fontes-e-achados.md`, seção 5) põe a Amil entre as fontes de parceria.

Ficou fora da configuração:

- o preço por POST (admin-ajax e `/wp-json/adesao/query`) e o gerador de PDF: não há tipo de captura para isso, e um tipo novo seria código;
- a Qualicorp e o amil.com.br, bloqueados no robots.txt;
- o institucional, que responde 403 ao agente.

`python -m coletor.fontes` valida sem problemas.

## Amostras e leitura

Pasta `amostras/operadoras/amil/` (origem e hash em `manifest.json`). Leitura geométrica, sem LLM. As duas amostras do Kit Corretor foram lidas no levantamento, mas não ficam no repositório: os termos de uso da Amil vedam aplicações automatizadas, e a amostra serve só para medir o leitor.

| Arquivo | Origem | Páginas | Preços lidos | Colunas (com registro ANS) | Confirmados pelo cálculo | Para revisão | Erros | Alertas |
|---|---|---|---|---|---|---|---|---|
| `amil_kit_manual_vendas_pme_2026-09.pdf` | Kit, página inicial (set/2026, versão 2026.10) | 61 | 0 | 0 | 0 | 0 | 0 | 1 (documento) |
| `amil_kit_linha_especial_pme_rj_2025-03.pdf` | Kit, avulso (mar/2025) | 5 | 324 de 360 | 36 (0) | 324 | 324 | 0 | 72 |
| `allcare_amil_adesao_df_2023-06.pdf` | Allcare, fora da página (jun/2023) | 11 | 60 de 60 | 6 (6) | 38 | 60 | 0 | 6 |

O que saiu de cada uma:

- **Manual de Vendas PME.** Zero preço é a leitura certa, e o leitor avisa no documento que não achou tabela de preço por faixa. O manual não tem essa grade: diz que a tabela do Kit é só referência e que o preço final sai na Plataforma Comercial. O conteúdo útil é de condição e só sairia pela leitura por LLM:
  - coparticipação por produto (30% a 40%, com limite por item);
  - reembolso (valor da URA × múltiplo por produto);
  - dois padrões de reajuste por faixa: a Tabela II vale para Bronze SP, RJ, SP Mais, DF e PR; a Tabela I, para os demais, incluindo o Bronze RJ Mais;
  - código interno de cada plano, carências e elegibilidade.
- **Linha Especial.** Os 324 valores lidos batem com o PDF. Nenhum tem registro ANS: a tabela usa o código interno da Amil (ex.: 969046), e o próprio PDF avisa que o código do plano "não pode ser o código do produto na ANS". As 36 colunas ficam para revisão por falta de produto.
  - Os nomes Fundamental, Essencial, Plena e Especial 200 existem como planos empresariais ativos da 326305. "Amil Fit" e "Amil Care" não aparecem com esse nome no índice.
- **Allcare Amil DF.** Os 60 valores batem com o texto da página e as 6 colunas ficaram com o registro certo, todos da 326305. Os 6 alertas são o achado esperado: produtos suspensos na ANS.
  - Suspensos desde 23/10/2023: 488.701/21-8 e 488.703/21-4 (Amil Fácil S80).
  - Suspensos desde 19/04/2024: 485.428/20-4, 485.426/20-8 e 485.422/20-5 (S380 e S450).
  - Suspenso desde 10/04/2025: 485.424/20-1.
  - O arquivo segue no ar sem link, com produtos que não aceitam contrato novo.

Problemas do leitor (código central):

1. **Faixa 59+ com o rótulo em duas linhas.** `amil_kit_linha_especial_pme_rj_2025-03.pdf`, páginas 1 e 2 (grade transposta, faixas nas colunas). O cabeçalho tem "59" numa linha e "ou +" na linha de baixo, junto dos "anos". `_RE_FAIXA` em `leitor/faixas.py` exige "59" seguido de "ou +", "ou mais" ou "+" no mesmo texto. As outras nove faixas foram reconhecidas.
   - A coluna 59+ se perdeu nas 36 linhas: 36 valores, com o alerta "faixas não lidas: 59+".
2. **Rótulo de coluna montado com texto de fora da grade.** `allcare_amil_adesao_df_2023-06.pdf`, página 4.
   - A coluna 488.701/21-8 ficou com "Obstetrícia faixa etária, estão rigorosamente da ANS. Amil Fácil S80 Enfermaria": puxou a observação acima da tabela.
   - S380 e S450 Enfermaria ficaram com o mesmo rótulo, "Amil NAC R Enfermaria".
   - Na Linha Especial, o nome do produto ocupa três linhas e o rótulo ficou partido: "968421 De 10 a 29 vidas", e "Amil Até 9 vidas" repetido para produtos diferentes.
   - O registro ANS salva a Allcare. Na Linha Especial, sem registro, os rótulos são o único jeito de saber o produto.
3. **Tolerância do cálculo.** `allcare_amil_adesao_df_2023-06.pdf`, página 4: 22 valores corretos ficaram sem confirmação.
   - 15 deles não têm colunas de referência suficientes para o cálculo.
   - Nos outros 7, o cálculo dá 2 ou 3 centavos de diferença (ex.: 1.400,71 contra 1.400,73; 5.733,03 contra 5.733,06).
   - A confirmação (`bate` em `leitor/calculo.py`) só aceita menos de 1,5 centavo, embora `leitor/conferencia.py` registre que o cálculo erra até 2 centavos quando a operadora arredonda em cadeia (`RUIDO_DO_CALCULO = 0.025`).

## Na ANS

Índice local (`dados/ans/indice.sqlite`, pda-008 de 30/09/2026). Operadora 326305: AMIL ASSISTÊNCIA MÉDICA INTERNACIONAL S.A., CNPJ 29.309.127/0001-79, medicina de grupo, SP, ativa.

| Situação | Coletivo empresarial | Coletivo por adesão | Individual ou familiar | Empresarial + adesão | Total |
|---|---|---|---|---|---|
| Ativo | 423 | 69 | 29 | 0 | 521 |
| Suspenso | 2.444 | 765 | 1.062 | 0 | 4.271 |
| Cancelado | 551 | 255 | 116 | 11 | 933 |
| Total | 3.418 | 1.089 | 1.207 | 11 | 5.725 |

- Dos 521 ativos, 127 são odontológicos. Ficam 394 planos médicos ativos: 344 empresariais, 49 de adesão e 1 individual. Na prática a Amil não vende plano médico individual.
- 335 ativos têm nota técnica (VCM por faixa) no índice; a nota mais recente é de 31/08/2026.
- Abrangência dos ativos: 255 empresariais nacionais e 146 por grupo de municípios; na adesão, 27 nacionais e 22 por grupo de municípios.
- 50 planos passaram a "Suspenso" em 2026.

## Lacunas e próximo passo

- **Preço vigente da 326305.** Não está em PDF fixo público. Caminhos, em ordem:
  1. autorização da Amil para ler o Kit (manual, e o JSON de preço por estado das chamadas `ktc_get_price_table_values` e `adesao/query`), ou envio da tabela por parceria;
  2. a caixa de e-mail do corretor que recebe os comunicados da Amil (modelo configurado com `@amil.com.br`);
  3. upload do PDF que o corretor baixa no Kit ("Baixar PDF" da tabela completa do estado).
- **Termos de uso.** Confirmar com a Amil ou com o jurídico se a cláusula contra automação vale para o domínio do Kit. Se não valer, as capturas do manual (página e arquivo da web) podem ser ativadas sem mudança de código.
- **Condições.** O Manual de Vendas PME muda a cada poucos meses: 5 versões entre julho de 2025 e setembro de 2026, contando a atual. Ler coparticipação, reembolso e carência dele depende da leitura por LLM, que não rodei.
- **Adesão.** Não achei canal público atual. A Supermed exige login, a Qualicorp bloqueia robôs e a Allcare tirou a Amil da página.
- **Leitor.** Corrigir o 59+ com rótulo em duas linhas e a montagem dos rótulos de coluna (itens 1 e 2 acima).
- **Não verificado:**
  - o texto integral dos termos de uso (403);
  - a lista oficial de planos ativos no institucional (403);
  - o preço por POST do Kit, que não chamei;
  - o manual Dental (Amil Dental também é 326305), que não baixei;
  - as tabelas das operadoras regionais do Kit (Ana Costa, Santa Helena, Sobam), que são de outros registros.
