# Pesquisa: fontes de dados, achados e embasamento

Consolidação da pesquisa feita em 29 e 30/09/2026, com agentes de IA trabalhando em paralelo e cada achado conferido por mim: dados abertos da ANS, sites públicos de 11 operadoras e administradoras, mercado e jurídico/regulatório. Aqui fica só o que foi verificado.

> **Atualização de 01/10/2026.** O mapeamento detalhado das 9 operadoras está em `docs/operadoras/`, uma por arquivo. Lá ficam os canais, a linha do robots.txt, as amostras lidas e os números da ANS. Ele corrige um ponto daqui e acrescenta outro:
> - a Smile (ESMALE, 395480) tem sede em Maceió/AL, e nenhum dos 28 produtos "DF" dela está ativo na ANS;
> - o Kit Corretor da Amil publica tabelas de outras operadoras do grupo, como a Ana Costa (360244), cancelada por incorporação em 06/2026.

**Convenções:** `[V]` = verificado com requisição, arquivo ou texto de norma; `[NV]` = não verificado ou inferido.

---

## 1. O Cotador (lp.cotadordeplanodesaude.com.br)

- **Produto e preço** [V]: SaaS por assinatura para corretores. R$ 77,90/mês ou R$ 41,41/mês no plano anual; plano empresarial sob consulta. "Todos os estados".
- **Operadoras citadas** [V]: Bradesco, SulAmérica, Unimed, Amil, Hapvida, Notre Dame, Smile, Saúde Sim e Quality ("entre outras"). As imagens incluem Allcare.
  - Smile, Quallity e Saúde Sim atuam no DF. Isso sugere que a base comercial é Brasília [NV].
- **Saúde Sim está extinta** [V]. `Relatorio_cadop_canceladas.csv`: registro 320111, "MASSA FALIDA DE SAÚDE SIM LTDA", cancelada em 2022-08-10, motivo "Liquidação Extrajudicial". Não consta no cadastro de ativas.
  - Exemplo direto do problema de desatualização.

---

## 2. Dados abertos da ANS: a espinha dorsal

Base de arquivos: `https://dadosabertos.ans.gov.br/FTP/PDA/`. É um índice Apache e aceita HTTP Range, então dá para extrair um único membro de um ZIP grande sem baixar tudo [V].

### 2.1 Datasets úteis

| Dataset | Caminho (sob /FTP/PDA/) | Tamanho | Atualização | Uso no cotador |
|---|---|---|---|---|
| Operadoras ativas | `operadoras_de_plano_de_saude_ativas/Relatorio_cadop.csv` | 339 KB, 1.106 linhas | diária | cadastro da operadora |
| Operadoras canceladas | `operadoras_de_plano_de_saude_canceladas/Relatorio_cadop_canceladas.csv` | 1 MB | diária | bloquear operadora extinta |
| Características dos produtos (pda-008) | `caracteristicas_produtos_saude_suplementar-008/pda-008-caracteristicas_produtos_saude_suplementar.csv` | 71 MB, 166.150 planos (28.932 ativos) | diária (D-1) | **catálogo mestre** |
| Municípios da cobertura | `…-008/pda-008-tabela_auxiliar_de_detalhamento_de_municipios.csv` | 69 MB | diária | área de cobertura por plano |
| Área de comercialização (NTRP) | `area_comercializacao_planos_ntrp/pda_area_comer_plano_ntrp.csv` | 1,1 GB | mensal | onde o plano é vendido e qual nota de preço vale |
| Histórico de situação | `historico_planos_saude/HISTORICO_PLANOS.csv` | 24 MB (cp1252) | mensal | ativo / suspenso / cancelado |
| VCM por faixa etária (NTRP) | `nota_tecnica_ntrp_vcm_faixa_etaria/nota_tecnica_vcm_faixa_etaria.zip` | 56 MB zip (23 CSVs, 2004–2026) | diária (D-1) | **preço de referência + banda legal** |
| Painel de precificação (031) | `painel_precificacao-031/pda-031-painel_precificacao.zip` | 121 MB → 2,57 GB | mensal | série de VCM e % de carregamento comercial |
| Faixa de preço | `faixa_de_preco/rel_faixa_de_preco.csv` | 1,8 MB | mensal | faixas $…$$$$$$ do mercado (percentis) |
| Rede hospitalar por produto | `produtos_e_prestadores_hospitalares/produtos_e_prestadores_hospitalares.zip` | 1,5 GB zip, 27 CSVs por UF (~19 GB) | ~semanal/mensal | **rede hospitalar por plano (CNES, CNPJ)** |
| Alterações de rede hospitalar (046) | `solicitacoes_alteracao_rede_hospitalar-046/pda-046-…-AAAA.zip` | 2026: 5,6 MB → 118 MB | mensal | **log de exclusões e substituições, com datas futuras** |
| Rede não hospitalar | `operadoras_e_prestadores_nao_hospitalares/….zip` | 1 GB | mensal | só por operadora, sem plano |
| Reajuste coletivo (RPC) | `RPC/pda-043-rpc-AAAAMM.csv` | ~50 MB/mês | mensal (~2 meses de defasagem) | % por contrato × plano |
| Reajuste do pool <30 vidas (055) | `percentuais_de_reajuste_de_agrupamento-055/…csv` | 594 KB | anual | reajuste PME por operadora (ciclo 2025: Amil 15,98%, Bradesco 15,11%, SulAmérica 15,23%, NotreDame 15,20%, Hapvida 11,50%) |
| Beneficiários (ICB/024) | `informacoes_consolidadas_de_beneficiarios-024/AAAAMM/pda-024-icb-UF-AAAA_MM.zip` | por UF | mensal (~5 semanas) | quais planos vendem agora (`QT_BENEFICIARIO_ADERIDO`) |
| API Operadoras | `https://www.ans.gov.br/operadoras-entity/v1/` (OpenAPI em `/v3/api-docs`) | JSON | on-line | consulta pontual. **Atenção: `ativa=0` devolve as ativas; `ativa=true` é bloqueado pelo WAF** |
| CNES (DataSUS) | `https://cnes.datasus.gov.br/EstatisticasServlet?path=BASE_DE_DADOS_CNES_AAAAMM.ZIP` | mensal | mensal | endereço e lat/long do prestador |

- **Teto do reajuste individual** 2026/27: **5,11%** (mai/2026–abr/2027). Série: 2022 15,50%; 2023 9,63%; 2024 6,91%; 2025 6,06% [V].
- O Guia ANS de Planos e a Consulta de Planos ao consumidor não têm API. São JSF com sessão, e o Guia usa Cloudflare Turnstile. **Não automatizar.** A Consulta de Planos é o único lugar em que aparece o motivo da suspensão (ANS × operadora) [V].

### 2.2 Colunas-chave

- **pda-008:** `ID_PLANO; CD_PLANO; NM_PLANO; REGISTRO_OPERADORA; RAZAO_SOCIAL; GR_MODALIDADE; PORTE_OPERADORA; VIGENCIA_PLANO; CONTRATACAO; GR_CONTRATACAO; SGMT_ASSISTENCIAL; GR_SGMT_ASSISTENCIAL; LG_ODONTOLOGICO; OBSTETRICIA; COBERTURA; TIPO_FINANCIAMENTO; ABRANGENCIA_COBERTURA; ID_GEO_COBERTURA; FATOR_MODERADOR; ACOMODACAO_HOSPITALAR; LIVRE_ESCOLHA; SITUACAO_PLANO; DT_SITUACAO; DT_REGISTRO_PLANO; DT_ATUALIZACAO`
  - `CD_PLANO` é o "Registro ANS do produto" do material comercial: `508805264` = **508.805/26-4**.
  - Chave para casar com o material comercial: `(REGISTRO_OPERADORA, CD_PLANO, 'P')` entre Ativo/Suspenso, que é única entre eles. **Nunca casar por nome** (344 nomes repetidos numa mesma operadora).
  - "Suspenso" = "ativo com comercialização suspensa".
  - Acomodação: "Coletiva" = enfermaria; "Individual" = apartamento.
- **VCM:** `CD_OPERADORA; ID_PLANO; CD_NOTA; DT_NTRP; ID_ABRG; FAIXA_ETARIA; VL_COMERCIAL_MENSALIDADE; VL_DESP_ASSISTENCIAL; VCM_MINIMO; VCM_MAXIMO; DT_ATUALIZACAO`
  - Decimal com ponto; datas dd/mm/aaaa.
  - `ID_ABRG` = UNICA | REGIONALIZADA. A regionalizada tem uma nota por região, e os municípios de cada nota vêm da área de comercialização.
  - Cobre 21.058 dos 21.059 planos ativos médico-hospitalares pré-estabelecidos (fora autogestão).
- **Rede hospitalar:** `ID_PLANO; CD_PLANO; ID_ESTABELECIMENTO_SAUDE; CD_CNPJ_ESTB_SAUDE; CD_CNES; NM_ESTABELECIMENTO_SAUDE; LG_URGENCIA_EMERGENCIA; DE_TIPO_CONTRATO; DE_DISPONIBILIDADE; CD_MUNICIPIO; SG_UF; DT_VINCULO_INICIO; DT_VINCULO_FIM…`
  - É um snapshot sem data de fim. **Exclusões já deferidas continuam listadas**; para remoções, a fonte é o log 046.
- **Log 046:** `ID_PLANO; CD_PLANO; TP_SOLICITACAO; MOTIVO; ID_PRESTADOR_EXCLUIDO; CNPJ_PRESTADOR_EXCLUIDO; CNES_PRESTADOR_EXCLUIDO; ID_PRESTADOR_INCLUIDO; …; RESULTADO; DT_ALTERACAO`
  - `DT_ALTERACAO` pode ser futura.
  - 2026 até agosto: 1.787 solicitações × 19.393 planos.

### 2.3 Normalizações obrigatórias

- **Operadora:** `str(x).strip().zfill(6)`. A área de comercialização traz `"\t5711"` e o monitoramento traz `6246`.
- **Encoding:** cp1252 na faixa de preço, no histórico, em penalidades e no CNES; o resto é UTF-8 com BOM.
- **Decimal:** ponto no VCM e na faixa de preço; vírgula no painel, no 054, no RPC e no agrupamento.
- **Faixa etária:** VCM usa `"00 a 18 anos"` … `"59 anos ou mais"`; painel e 054 usam código 1..10.

### 2.4 Receitas de detecção de mudança

| Evento | Fonte | Como detectar |
|---|---|---|
| Plano novo | pda-008 (diário) | `ID_PLANO` novo e Ativo. 448 registros entre 01/08 e 28/09/2026 |
| Plano suspenso ou cancelado | pda-008 `SITUACAO_PLANO` / `DT_SITUACAO` | diff diário por `ID_PLANO` |
| Operadora cancelada | CADOP canceladas (diário) | bloquear cotação |
| Hospital sai da rede | log 046 (mensal, **datas futuras**) | avisar o corretor antes de a mudança valer |
| Preço de referência mudou | VCM (nova `CD_NOTA` / `DT_NTRP`) | revalidar a tabela de venda contra a nova banda |
| Reajuste PME / coletivo | 055 (anual) / RPC (mensal) | prever a próxima tabela |

### 2.5 Regras de validação com base legal

1. **Faixas etárias**: RN 563/2022, que revogou a RN 63/2003 com as mesmas regras.
   - As 10 faixas: 0–18, 19–23, 24–28, 29–33, 34–38, 39–43, 44–48, 49–53, 54–58, 59+.
   - I: `v10 ≤ 6·v1`.
   - II: `v10/v7 ≤ v7/v1`, ou seja, `v10·v1 ≤ v7²` (variação relativa).
   - III: sem variação negativa.
   - Nas NTRPs de 2022 a 2026 há só 5 violações em 150 mil notas; a mediana de v10/v1 é 6,0.
2. **Banda de preço**: RN 564/2022, arts. 5º e 6º §2º.
   - `max(0,7·VCM, despesa assistencial) ≤ preço de venda ≤ 1,3·VCM`.
   - `VCM_MINIMO` e `VCM_MAXIMO` já vêm prontos no arquivo e batem 100% com a regra.
3. **Situação**: só cotar plano Ativo de operadora ativa. Suspenso não aceita contrato novo, salvo as exceções da RN 543/2022 art. 12.
4. **Atributos**: contratação, acomodação, coparticipação, abrangência, obstetrícia e livre escolha devem bater com o pda-008.
5. **Carências**: Lei 9.656/98 art. 12, V.
   - Máximos: parto a termo 300 dias; demais casos 180 dias; urgência/emergência 24 h.
   - CPT até 24 meses (art. 11 + RN 558/2022).
   - Coletivo empresarial com 30 ou mais vidas e ingresso em até 30 dias: sem carência e sem CPT (RN 557/2022).
   - Adesão com ingresso em até 30 dias da celebração ou do aniversário do contrato: sem carência (art. 17).
6. **Rede**: o hospital anunciado deve constar na rede do plano e **não** ter exclusão deferida vigente no log 046.
7. **Reajuste individual** acima do teto do ciclo é inconsistente.

### 2.6 O que NÃO é público

- tabela de preço de venda vigente (há só o VCM de referência com a banda);
- % de coparticipação;
- tabela de reembolso;
- carências praticadas;
- rede não hospitalar por plano;
- serviços por hospital;
- motivo da suspensão;
- elegibilidade de adesão (entidades e profissões).

**Isso é exatamente o que vem nos PDFs de tabela de venda.**

---

## 3. Sites públicos das operadoras

A **chave comum** é o **número de registro ANS do produto**. Aparece na Quallity, na Unimed (nome do plano), na Smile (por prestador), na Hapvida e NotreDame (é o próprio filtro), na Amil (ProdutosAns), no Bradesco (`codigoProduto`) e nos PDFs.

| Operadora | Rede por plano, pública | Como o site expõe | Proteções e termos | Preço público | Caminho |
|---|---|---|---|---|---|
| **Quallity Pró Saúde** (ANS 418170) | Sim | busca de rede aberta, com o nº ANS de cada plano | nenhuma; sem robots.txt; sem termos restritivos | só "a partir de" | coletor direto |
| **Smile** (ANS 395480) | Por linha de produto | formulário HTML, com o nº ANS por prestador | aviso de "uso exclusivo" | não | coletor direto, com cuidado |
| **Hapvida** | Sim, filtrada pelo próprio registro ANS | busca dinâmica | reCAPTCHA na busca; robots.txt permite | "a partir de"; simulador pede dados pessoais | **só com autorização** |
| **NotreDame (GNDI)** | Sim, no mesmo sistema da Hapvida | busca dinâmica | idem | PDFs oficiais defasados | só com autorização |
| **Unimed (guia nacional)** | Sim | busca com sessão | **termos proíbem "reprodução, cópia, arquivamento"**; robots.txt bloqueia `/site/documents/` | PDFs de algumas cooperativas (ex.: Guarulhos) | **parceria** |
| **Unimed-BH** | Por linha de produto | aplicação que muda a cada atualização do site | frágil | não | média |
| **Bradesco Saúde** | Busca atrás de reCAPTCHA | lista de planos com o registro ANS; página pública de "planos por referenciado" | reCAPTCHA; robots.txt `Allow: /` | não | média |
| **SulAmérica** | Busca com reCAPTCHA a cada pesquisa | busca por raio | termos sem cláusula anti-robô | não | **parceria** |
| **Amil** | Sim | API própria, que bloqueia acesso fora do navegador | **termos proíbem automação** | PDFs antigos (2018–2020) | **parceria** |
| **Porto** | Sim | serviço por plano, atrás de WAF | termos vedam cópia e **compilação** | não | baixa |
| **Allcare** (administradora, ANS 417459) | Não tem rede própria | página de materiais com **56 PDFs públicos**, com a data da versão no nome do arquivo | robots.txt permite; sem termos restritivos | **Sim** | **melhor fonte de preço de adesão** |

A rede hospitalar acabou vindo de outro lugar: a ANS publica a rede de cada plano nos dados abertos (seção 2), sem depender dos sites, que mudam e às vezes bloqueiam robôs. Os sites ficam para o que a ANS não tem.

**Outras observações:**
- **Divergência entre fontes oficiais** [V]: para o mesmo produto em BH, o guia nacional da Unimed mostra 22 hospitais e o guia da Unimed-BH mostra 6.
- **Páginas de "movimentação de rede"** (RN 585): Amil, SulAmérica, Bradesco, Smile e Quallity publicam as mudanças de rede. Para hospital, a fonte única e oficial é o registro de pedidos de alteração de rede da ANS (seção 2).
- **Lista oficial de produtos ativos da Amil** (PDF, set/2026) [V]: `institucional.amil.com.br/sites/institucional/files/2026-09/Lista_planos_operadora_ativos_092026.pdf`, com 533 produtos.
- **Portais de corretor** (login): Hapvida (Planium), NotreDame (Salesforce), Bradesco (Portal de Negócios), Amil (portalcorretor), Quallity (WebPlan + Planium) e Allcare (portal + AllTech).

---

## 4. Mercado

- **Concorrentes** [V]:
  - Simulador On-Line: "35 mil corretores". Tem feed público de mudanças de tabela.
  - Painel do Corretor (Agger, que comprou a Trindade em 2025): "+750 operadoras", R$ 79/mês.
  - Cotador Simplificado (Fortaleza): "1.600+ consultores".
  - Outros: SIMP, CorretorCRM, Soll/Kuint (WhatsApp; declara usar sites de operadoras e a ANS), Hannah IA (Affix, WhatsApp), beneficios.ai e Baeta ("mesa técnica" semanal).
  - Click Planos (B2C, ~130 operadoras) disse à Forbes (29/09/2026) que recebe PDFs das administradoras e extrai com IA.
- **Volume de mudança** [V]: o feed do Simulador On-Line tem ao menos **225 avisos de alteração de tabela entre 01/01 e 25/09/2026**, em 106 dias distintos: 93 reajustes, 61 produtos novos e 14 suspensões.
- **Não existe padrão ou API setorial de cotação em saúde** [V/NV]. As APIs de SulAmérica, Bradesco e Porto são para parceiros e pós-venda.
  - A Planium, do lado da operadora, tem 150+ operadoras e cerca de 10% das vendas; é um canal plausível de parceria.
  - No seguro auto, o multicálculo usa webservice autorizado ou "robô" com o login do corretor.
- **Universo** [V]: 1.106 operadoras ativas (262 cooperativas médicas, 252 medicina de grupo, 183 administradoras…). 53,2 milhões de contratos (jul/2026).

---

## 5. Jurídico e regulatório

- **RN 486/2022** (revogou a RN 285/2011) [V]:
  - a operadora deve publicar no portal a **rede por plano** (nome, nº ANS), com dados do prestador;
  - **"atualizados em tempo real"**;
  - **vedado restringir o acesso a beneficiários**;
  - mapas acima de 20 mil beneficiários.
  - É a base mais forte para coletar rede de páginas públicas.
- **RN 585/2023** [V]: mudança de rede hospitalar deve ser comunicada com **30 dias** de antecedência, em espaço específico do portal.
- **LGPD** [V]:
  - dado público exige finalidade, boa-fé e interesse público (art. 7º §3º);
  - base em legítimo interesse + minimização;
  - médicos PF são dado pessoal. **Coletar só PJ (hospitais, laboratórios) e descartar CPF, CRM e e-mail.**
  - A ANPD prioriza "agregadores de dados" e raspagem no Mapa de Temas 2026–2027.
- **Lei de Direitos Autorais** [V]: não protege os dados em si (art. 7º §2º). Extrair fatos (preço, faixa, carência) é defensável; copiar layout, textos e logos, não.
- **Concorrência desleal** (LPI art. 195): casos Catho (R$ 13,6 mi e R$ 21,8 mi) e Webmotors × Websis envolveram **base de concorrente** e acesso indevido.
  - O TJRS (Escavador, 2020) admitiu republicar dado público.
- **Termos de uso**: a Amil proíbe automação expressamente. No Brasil não há jurisprudência específica sobre termos anti-raspagem [NV].
- **Credencial do corretor** (robô com o login dele): é uso de mercado no seguro auto.
  - Riscos: termos do portal, dados de beneficiários (dado sensível), confidencialidade e guarda de senha.
  - Precedente: TCC Bradesco × GuiaBolso no CADE (2020).
  - Só como ponte, com opt-in, escopo mínimo e sem dados de clientes.
- **Open Health**: só o relatório do GT de 2022; não saiu do papel. O Open Insurance (SUSEP) não cobre saúde.
- **Venda online obrigatória** (CP 145, dez/2024): o próprio relatório de impacto da ANS aponta assimetria de informação e falta de comparabilidade de preço. Foi adiada e suspensa judicialmente.
- **Agenda Regulatória 2026–2028**: "transparência e qualidade de dados" (2º tri/2027) e estudo sobre o modelo de envio da NTRP.

**Linhas vermelhas da proposta:**
- não fazer login;
- não contornar captcha, WAF ou bloqueio;
- respeitar robots.txt e termos;
- não coletar dados pessoais de beneficiários;
- **nunca coletar de outros cotadores**;
- onde os termos proíbem (Amil, Unimed, Porto): parceria.

---

## 6. Testes já feitos com dados reais

1. **Unimed Guarulhos PME 2026 × ANS** [V]:
   - os **12 produtos** do PDF foram achados no pda-008 pelo registro, todos Ativos (operadora 333051), com contratação, acomodação, fator moderador e abrangência;
   - dos **360 preços** (3 tabelas × 12 produtos × 10 faixas), **359 estão dentro da banda** da nota técnica vigente (notas de 23–26/12/2025);
   - **1 está abaixo do piso**: 478.590/17-8 (Essencial III Enfermaria), faixa 0–18, tabela de 30–99 vidas, R$ 116,56 contra o mínimo de R$ 122,77 (VCM R$ 136,32). A página diz "tabela passível de negociação";
   - a ANS indica "Franquia + Coparticipação" em produtos que o PDF chama de "coparticipação parcial" com internação isenta. É um atributo a conferir por uma pessoa, não um erro.
2. **Regras de faixa (RN 563)**:
   - Unimed Guarulhos: 36 de 36 colunas passam, **com tolerância de 0,1%**. A operadora usa o limite exato, e o arredondamento em centavos estoura por pouco;
   - Allcare Hapvida PME DF: passa.
3. **Falso positivo instrutivo**: a tabela Hapvida adesão DF (Allcare) "viola" a regra II em 6 de 6 colunas porque o preço **embute odonto** ("Com Odonto"). Somar um valor fixo a todas as faixas distorce as proporções. O validador precisa conhecer a composição do preço e gerar **alerta**, não erro.
4. **A validação pegou um bug do próprio parser**: a regex não reconhecia "0 a 18" com um dígito, deslocou as faixas, e as regras de faixa acusaram na hora.
