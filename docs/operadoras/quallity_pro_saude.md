# Quallity Pró Saúde (ANS 418170)

Levantamento de 01/10/2026. Slug: `quallity_pro_saude`.

> **Depois deste levantamento**, o que ele apontou no leitor e no coletor foi corrigido no código, cada caso com teste (`docs/proposta.md`, seção 7):
> - a vigência impressa ("vigente 08/2022") passou a ser lida sem LLM;
> - a conferência passou a usar a nota técnica plausível para a data do material: a tabela de 2022 deixa de ter 21 alertas de preço contra a nota de 2026, e o que aparece é o aviso de nota técnica nova depois do material, que é o sinal certo de tabela defasada;
> - o guia de coparticipação, sem grade de preço, passou a gerar aviso.

## Resumo

O registro confere: 418170 é da QUALLITY PRÓ SAÚDE PLANO DE ASSISTÊNCIA MÉDICA LTDA. (CNPJ 09.433.795/0001-04), medicina de grupo, Brasília/DF, ativa.

A operadora não publica tabela de preço. No site saem duas condições comerciais em PDF: o guia de coparticipação (versão 01/09/2026) e o reajuste do agrupamento de contratos com menos de 30 vidas (9,76% em 2026). A tabela de adesão pública é a que o Sinpro-DF mantém na notícia do convênio. É material da Platinum Administradora, impresso "vigente 08/2022", e é a única captura ativa.

Rota recomendada para preço vigente: caixa de e-mail que receba as tabelas da Quallity e da Platinum (modelo inativo), ou parceria. O portal do corretor (WebPlan e Planium) exige login.

**Divergências a apontar no radar**

- **Plano suspenso exibido como ativo.** A busca de rede da própria operadora mostra 37 planos marcados "ATIVO". Sete deles estão suspensos na ANS desde 03/09/2026: 491.936/22-0, 497.661/23-4, 497.662/23-2, 497.664/23-9, 497.665/23-7, 499.086/24-2 e 500.011/24-4.
- **Preço anunciado abaixo do piso.** O site anuncia "a partir de R$ 162,28" para o Gold Life adesão 0–18 anos. O piso da nota técnica vigente (410599, de 08/01/2026) é R$ 165,24, com VCM de R$ 204,76.

## Canais verificados

| Canal | Endereço | O que tem | robots.txt / termos | Situação |
|---|---|---|---|---|
| Site da operadora | https://www.quallityprosaude.com.br/ | Institucional e "a partir de R$ 162,28". O simulador é formulário de contato com nome e telefone (não enviado). | `User-agent: *` / `Disallow: /wp-admin/` / `Allow: /wp-admin/admin-ajax.php`. Nenhum termo restritivo encontrado. | Público, sem tabela |
| Coparticipação | https://www.quallityprosaude.com.br/coparticipacao/ | Guia em PDF, versão 01/09/2026 (data no nome do arquivo), 100 páginas | Idem | Público. Captura configurada, inativa |
| Reajustes | https://www.quallityprosaude.com.br/reajustes/ | 5 PDFs, de 2023 a 2026, do reajuste do agrupamento com menos de 30 vidas. O de 2026 tem 188 páginas, código do contrato (sem nome de empresa), plano, registro ANS, mês e 9,76%. | Idem. Os links levam `?v=<timestamp>`, que muda a cada carga da página (1790827262 e depois 1790828343). | Público. Captura configurada, inativa |
| Publicações e manuais | /publicacoes/, /manuais/ | Demonstrações financeiras, IDSS, manual do aplicativo | Idem | Fora do escopo |
| Busca de rede | https://facgeo.quallity.srv.br/ | Lista de 37 planos com registro ANS e "ATIVO"; busca de prestador por plano | robots.txt responde 404 | Público; 7 planos divergem da ANS |
| Portal do corretor | webplan.quallity.srv.br, quallityprosaude.planium.io | Login | Não se aplica | Restrito, não acessado |
| Platinum Administradora (ANS 418986) | https://platinumbeneficios.com.br/ | Página de produtos. A cotação é formulário com nome, e-mail e telefone. Os únicos PDFs são o manual de orientação para contratação e o guia de leitura contratual. Mesmo endereço da Quallity. | `Disallow: /wp-admin/` | Sem tabela pública |
| Sinpro-DF | https://www.sinprodf.org.br/sinpro-firma-convenio-com-a-quallity-e-professor-sindicalizado-tera-uma-serie-de-beneficios/ | Notícia de 20/05/2019 com link "confira tabela de adesão" para `wp-content/uploads/2019/05/Tabela-de-vendas-quallity.pdf`. O arquivo foi trocado no mesmo endereço e hoje diz "vigente: 08/2022" (Last-Modified 31/01/2023). | `Disallow: /wp-admin/` | Captura ativa |
| Arquivo da web: site da operadora | API CDX, domínio quallityprosaude.com.br | 100 PDFs guardados: manuais, demonstrações, reajustes de 2015 a 2026. Os "tabela_2015_2.pdf" a "tabela_20170126.pdf" são relatórios de reajuste (11,95% em 2015/16, 23,57% em 2016/17), não tabelas de venda. | Permite | Sem tabela de venda |
| Arquivo da web: cópia do Sinpro | `cdn.sinprodf.org.br/.../Tabela-de-vendas-quallity.pdf` (cópia de 02/08/2024) | Mesma tabela de 08/2022 | O robots.txt de cdn.sinprodf.org.br responde 403 e o projeto trata isso como proibido | Não usar |
| Comparadores e corretoras | medlifeseguros.com.br, planosdesaudedf.com.br, gruposaudebrasil.com, planodesaudebrasiliadf.com.br, seu-convenio.com, SlideShare (proposta enviada por terceiro) | Preços de 2024 e 2025 transcritos em HTML | Não se aplica | Não usados (regra do projeto) |

## Captura configurada

Arquivo: `fontes/operadoras/quallity_pro_saude.json`.

- **Sinpro-DF (convênio Quallity)** (`pdf_administradora`): `pagina_publica` **ativa** na notícia do convênio.
  - Usa `incluir` `(?i)quallity[^/]*\.pdf$` para não pegar os outros PDFs da barra lateral do Sinpro.
  - A descoberta ao vivo achou 1 candidato e o robots.txt permite.
  - Pega a troca do arquivo no mesmo endereço, que já aconteceu uma vez, e um link novo se o Sinpro mudar.
- **Quallity Pró Saúde** (`site_operadora`):
  - `pagina_publica` **inativa** para `/coparticipacao/` (incluir `/wp-content/uploads/.*coparticipacao.*\.pdf$`). A descoberta funciona (1 candidato, data 01/09/2026 lida do nome) e o robots.txt permite. Ficou inativa porque o guia tem 100 páginas, 96 delas de lista TUSS. Ativa, a captura mandaria o PDF inteiro para a leitura dupla, com custo de LLM em cada versão, e a leitura geométrica não extrai regra de coparticipação. Ligar quando houver leitura de condição limitada às primeiras páginas.
  - `pagina_publica` **inativa** para `/reajustes/`. A descoberta funciona (5 candidatos), mas o `?v=` que muda a cada carga faz o motor tratar os 5 PDFs como novos em toda coleta: baixa de novo cerca de 6 MB e cria item novo. Além disso, não são tabelas de preço.
  - `caixa_email` **inativa** como modelo. Remetentes: `@quallityprosaude.com.br` e `@platinumbeneficios.com.br`, os domínios de e-mail que as duas cadastram na ANS.
- `python -m coletor.fontes` valida sem problemas.

## Amostras e leitura

Pasta `amostras/operadoras/quallity_pro_saude/` (hash e origem em `manifest.json`). Saídas em `saidas/`.

| Arquivo | Páginas | Preços lidos | Colunas (com registro ANS) | Confirmados pelo cálculo | Para revisão | Erros | Alertas |
|---|---|---|---|---|---|---|---|
| `sinpro_quallity_adesao_ambulatorial_df_2022-08.pdf` | 2 | 40 de 40 | 4 (4) | 29 | 30 | 0 | 21 |
| `quallity_coparticipacao_2026-09-01.pdf` | 100 | 0 | 0 | 0 | 0 | 0 | 0 |

O que o leitor fez:

- **Tabela do Sinpro.** Os 40 valores conferem com o PDF: Pró Saúde Platinum 476.610/16-5, Gold Plus 480.598/18-4, Gold Plus Mais 489.426/21-0 e Gold Plus Mais SINPRO, com o mesmo registro 489.426/21-0. Os quatro produtos estão ativos na ANS.
- **Os 21 alertas mostram que a tabela está defasada.** Para três colunas, os preços das faixas de 0 a 43 anos ficam abaixo da despesa assistencial da nota técnica de 08/01/2026. No conjunto, essas colunas ficam 33%, 35% e 44% abaixo do VCM, fora da banda de ±30% em 4 faixas cada.
- **Guia de coparticipação.** Levou 20 s e não achou grade, o que está certo: não é tabela por faixa.

Problemas do leitor:

1. **Vigência impressa ignorada.** Arquivo `sinpro_quallity_adesao_ambulatorial_df_2022-08.pdf`, página 1: a linha "Tabela atual vigente: 08/2022" não gera aviso de documento. Sem a leitura por LLM a vigência não é extraída, e a defasagem só aparece pela banda de preço da ANS.
2. **Mesmo registro em duas colunas, sem condição que as separe.** Na página 1, as colunas "Gold Plus Mais" e "Gold Plus Mais SINPRO" têm preços diferentes e `condicao` vazia nas duas. O preço exclusivo da entidade não vira marca de condição; a comparação entre versões depende da ordem das colunas.
3. **Rótulos com texto do título.** Na página 1 o leitor gerou "DE QUALLITY Plus Mais SINPRO" (perdeu "Gold") e "VENDAS AMBULATORIAL Gold Plus". É só cosmético.
4. **Documento de condição passa calado.** O arquivo `quallity_coparticipacao_2026-09-01.pdf` termina com 0 preços e nenhum aviso de documento. A tabela de valores por grupo da página 1 não é extraída. No pipeline, com chave de API, as 100 páginas iriam para o LLM. Sugestão para o código central: detectar documento sem grade de faixa etária e limitar ou pular a segunda leitura.
5. **Lacuna no próprio guia, não no leitor.** O anexo classifica 2 códigos no grupo "Consultas por telemedicina", que não tem valor na tabela da página 1. Uma pessoa precisa conferir.

O PDF de reajuste de 2026 não entrou como amostra porque não é material de venda. O texto foi lido em memória, sem gravar, só para conferir o conteúdo: código do contrato, plano, registro ANS, mês e 9,76%, sem nome de empresa.

## Na ANS

Índice local `dados/ans/indice.sqlite` (pda-008 de 30/09/2026) e CADOP.

- Operadora ativa, registrada em 15/08/2011.
- 62 planos: 43 ativos, 17 suspensos e 2 cancelados.

| Contratação | Ativo | Suspenso | Cancelado |
|---|---|---|---|
| Coletivo empresarial | 22 | 5 | 2 |
| Coletivo por adesão | 21 | 10 | 0 |
| Individual ou familiar | 0 | 2 | 0 |

- **Ativos:**
  - Segmentação: 17 ambulatorial + hospitalar com obstetrícia, 12 só ambulatoriais, 6 odontológicos, 3 ambulatorial + odonto, 3 ambulatorial + hospitalar + odonto e 2 de referência.
  - Fator moderador: 14 com coparticipação.
  - Abrangência: 41 municipais.
  - 37 têm nota técnica (os 6 sem nota são os odontológicos); a mais recente é de 20/07/2026.
- **Mudanças recentes:**
  - 8 suspensões em 03/09/2026: os 7 que a rede ainda mostra como ativos e o 499.085/24-4.
  - Planos novos: 508.771/26-6 (25/07/2026), 508.181/26-5 (18/05/2026), 506.975/25-1 e 506.976/25-9 (02/12/2025), 506.834/25-7 (12/11/2025).
- **Ativos fora da lista da rede:** 13 planos ativos na ANS não aparecem na lista da busca de rede, entre eles PROSAUDE ADESÃO e EMPRESARIAL, os Master Green/Gold AC/AS e QUALLITY PRIMEIRO CUIDADO (empresarial).
- **Nome grafado diferente:** a ANS registra "MATER ESPECIAL - AS" (497.661/23-4); a rede mostra "MASTER ESPECIAL - AS". O casamento por registro resolve.

## Lacunas e próximo passo

- **Sem tabela vigente pública.** Nenhuma tabela de preço atual da Quallity é pública, nem de adesão nem empresarial. A de 08/2022 serve para conferir a defasagem, não para cotar.
  - Próximo passo: caixa de e-mail com remetentes `@quallityprosaude.com.br` e `@platinumbeneficios.com.br`, ou parceria com a Platinum.
- **Ligar as duas capturas inativas do site** depois de mudanças no código central:
  - coparticipação: leitura de condição limitada às primeiras páginas;
  - reajustes: identificar o item sem a query `?v=`.
- **Não verificado:**
  - se o Sinpro ainda aplica a tabela de 08/2022 a novos associados (a notícia de 22/11/2024 fala em "tabelas exclusivas", sem link);
  - os municípios cobertos por plano, que não estão no índice local.
- **Rede como fonte de conferência:** a busca de rede (facgeo) responde JSON por plano. Não há tipo de captura para isso no `coletor/`. Seria a fonte para conferir a rede anunciada contra a ANS.
