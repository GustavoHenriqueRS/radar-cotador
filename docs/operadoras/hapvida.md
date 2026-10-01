# Hapvida (ANS 368253)

Levantamento de 01/10/2026. Slug: `hapvida`. Configuração em `fontes/operadoras/hapvida.json`; amostras em `amostras/operadoras/hapvida/`.

> **Depois deste levantamento**, o que ele apontou no leitor e no coletor foi corrigido no código, cada caso com teste (`docs/proposta.md`, seção 7):
> - o tipo de captura `api_json` foi escrito, e a API da CORPe trouxe as 53 tabelas Hapvida, cada uma com a data da versão. No teste às cegas, os 3.000 preços da leitura geométrica foram todos confirmados pelo LLM;
> - "com coparticipação total ou parcial" deixou de marcar a grade inteira como "total";
> - o negrito falso (letra desenhada duas vezes no mesmo lugar) deixou de esconder a segunda grade da tabela de Belo Horizonte.

## Resumo

A Hapvida não publica tabela de preço. O material de venda fica no Conecta Corretor e no portal de vendas Planium, ambos com login; o site aberto mostra só "planos a partir de" e as carências do plano individual. O que é público chega pelas administradoras: Allcare (já coletada, 43 tabelas em 15 UFs), Affix, CORPe e Safe. A rota recomendada é manter a Allcare, somar a Affix pelo arquivo da web e a página da Safe, e escrever um tipo de captura para a API aberta da CORPe, que tem 53 tabelas Hapvida com data no nome. Cuidado com a marca: "Hapvida" cobre seis registros na ANS, e as tabelas "Hapvida NotreDame" de SP e RJ trazem produtos da NotreDame Intermédica (359017), mesmo quando a capa cita 368253.

## Canais verificados

| Canal | Endereço | O que tem | robots.txt / termos | Situação |
|---|---|---|---|---|
| Hapvida, Área do Corretor | https://www2.hapvida.com.br/corretor | Atalhos para o Conecta Corretor (CPF e senha), o Portal de Venda Super Simples e PME (hapvida.planium.io, login), comissões e cadastro de empresa. Nenhum PDF de tabela. | `www2.hapvida.com.br` libera `/corretor` e as páginas de planos; bloqueia `/web`, `/w`, `/busca`, `/login`, `/portal-adm`. | Restrito (login) |
| Hapvida, páginas de planos | https://www2.hapvida.com.br/planos-de-saude-individuais e `/planos-de-saude-micro-empresa` | "A partir de R$ 105,30/mês" (individual: Nosso Plano, Nosso Médico, Mix, Pleno) e "R$ 93,79/mês" (PME: Smart, Nosso Médico). Carências do individual (24 h urgência e consultas; 30 dias raio-x e ECG; 60 dias odonto; 90 dias exames especiais; 180 dias internação e alta complexidade; 300 dias parto). Simulação e cotação só por formulário (não aberto). | Permitido. | Público, sem tabela |
| Site antigo de vendas, arquivo da web | `www.hapvida.com.br/site/vendas/sites/default/files/` | 110 arquivos guardados: banners, ícones, termos de odonto. Nenhuma tabela de preço. | `www.hapvida.com.br` libera tudo para `*`. | Sem tabela |
| Allcare | https://www.corretorallcare.com.br/materiais-de-vendas | 43 tabelas Hapvida (22 de adesão, 21 de PME) em AL, BA, CE, DF, GO, MA, MG, PA, PB, PI, RJ, RS, SC, SE e SP; 13 marcadas "em atualização". | Permite. | Já coletada (não alterada) |
| Affix | Sem página que liste; PDFs em `affix.com.br/wp-content/uploads/` | Manuais do corretor por praça: adesão, PME via Affix Empresas e grupos do setor público (prefeituras, PM, bombeiros), com preço, coparticipação, carência e área de comercialização. No arquivo da web: 627 nomes de arquivo Hapvida desde 2020; 51 cópias de 2026, em 16 UFs (inclui AM, PE e RN, que a Allcare não cobre). | robots.txt libera tudo. Os termos (cl. 3.3) vedam reproduzir ou distribuir material de venda sem autorização, e o PDF se diz "de uso interno destinado exclusivamente aos consultores", embora esteja aberto. | Público; configurado pelo arquivo da web |
| CORPe Saúde | API https://api.corporeadministradora.com.br/api/support_material/listSupportMaterial (a página `corpesaude.com.br/site/tabelas-e-entidades` é uma SPA sem links no HTML) | 53 tabelas Hapvida: adesão em 26 praças, PME em 26 praças e CCG no RS. Data da versão no começo do nome (`07.05.2026_`, `15.09.2026_`, `24.02.2026_`). | Os dois domínios liberam tudo. | Público; sem tipo de captura para JSON |
| Safe | https://safeadmin.com.br/produtos/hapvida/ | 3 PDFs de adesão: Rio de Janeiro, Entidades SP, Interior e Litoral SP. Endereço sem data (o buscador ainda indexa cópias antigas em pastas por mês, como `/uploads/2026/01/`). | robots.txt só bloqueia `/wp-admin/`. Os termos vedam copiar, republicar ou redistribuir conteúdo sem autorização prévia. | Público; configurado. A tabela do RJ traz produtos da 359017 |
| UniCor Benefícios | https://www.unicorbeneficios.com.br/hapvida.html | Página institucional; a "Área de Vendas" é o Planium (login). Tabelas Hapvida da UniCor (BH, Uberlândia, Goiânia, Anápolis, Limeira, Curitiba) aparecem só no site de uma corretora (`rotaseguros.com.br/corretor/wp-content/uploads/`). | robots.txt libera. | Restrito na fonte; cópias de terceiro não usadas |

Pedidos feitos com o `Http` do projeto: no máximo 12 por site (Affix e arquivo da web); 10 na Safe e menos de 5 nos sites da Hapvida, da CORPe e da UniCor.

## Captura configurada

- **Hapvida** (fonte nova, `pdf_operadora`): só o modelo de `caixa_email`, desligado, com remetente `@hapvida.com.br` (domínio dos e-mails publicados em https://www2.hapvida.com.br/atendimento/saude). A operadora entrega o material ao corretor credenciado; sem conta, o caminho é a caixa que recebe esses envios ou uma parceria via Planium.
- **Safe** (fonte existente, só a captura nova): `pagina_publica` em `/produtos/hapvida/`, filtrando PDFs com "hapvida" no nome. Ativa: a descoberta ao vivo achou os 3 PDFs. O nome não tem data; a versão sai do conteúdo e do Last-Modified.
- **Affix** (fonte existente, só a captura nova): `wayback` sobre `https://affix.com.br/wp-content/uploads/`, PDFs com "hapvida" no nome, cópias desde 2026. Ativa: a descoberta ao vivo achou 51 manuais. A Affix não tem página que liste os manuais, e o nome do arquivo muda a cada versão (`-01-26`, `-03-26`, `-10-25-1`), então endereço fixo não serve. O `data_no_nome` foi escrito para tirar da chave de série a pasta do WordPress e o sufixo de versão, assim `...AD-Manual-TERESINA-01-26.pdf` e `...AD-Manual-TERESINA-02-26.pdf` caem na mesma série; a data da versão fica a da primeira cópia no arquivo, porque o sufixo não tem dia nem ano com quatro dígitos.
- **CORPe** (fonte existente, captura nova feita depois deste levantamento): `api_json` sobre a API aberta da página de tabelas, filtrada em "hapvida". Ativa: 53 tabelas, cada uma com a data da versão no começo do nome.
- **Não configurado**: UniCor (login) e o site da Hapvida (não há PDF de preço).

## Amostras e leitura

Leitura geométrica, sem LLM, com o código do leitor de 01/10/2026 01h38 (ele mudou durante o levantamento; os números abaixo são iguais nas duas rodadas).

| Arquivo | Origem | Conteúdo | Preços | Colunas com registro | Revisão | Erros / alertas |
|---|---|---|---|---|---|---|
| `affix_hapvida_pme_pe_2026-03.pdf` | Affix, manual PME Recife "03-26" | 3 produtos Nosso Plano da 368253, cada um com coparticipação total e parcial | 60 | 6 de 6 | 10 | 0 / 1 |
| `corpe_hapvida_pme_am_2026-02-24.pdf` | CORPe, PME boletado Manaus, "v.fevereiro.2026" | os mesmos 3 registros, preços de Manaus | 60 | 6 de 6 | 0 | 0 / 0 |
| `safe_hapvida_adesao_rj_2026-03.pdf` | Safe, adesão RJ | 12 produtos Smart, Advance e Premium, todos da NotreDame (359017) | 260 | 26 de 26 | 131 | 0 / 123 |

Os valores lidos batem com o texto do PDF nas três amostras (60, 60 e 260; a coluna de cada valor foi conferida na primeira e na última faixa). Os registros da Affix e da CORPe existem e estão ativos na 368253. O alerta da Affix é de banda: 484.248/19-1 com coparticipação parcial fica 37% acima do VCM da nota de 28/09/2026. Na Safe, 114 alertas são de "faixa fora do padrão": a curva etária da tabela é mais achatada que a da nota técnica, com as faixas jovens caras em relação ao VCM (ex.: 476.794/16-2, 0 a 18 a 2,48 vezes o VCM e as demais faixas perto de 1,89); 9 são de banda (±30%) com nota de 14/09/2026. Não é erro de leitura.

Problemas do leitor:

1. `affix_hapvida_pme_pe_2026-03.pdf`, p. 2: o cabeçalho "COPARTICIPAÇÃO | TOTAL | PARCIAL" cobre três colunas de cada lado, e o leitor não separa total de parcial. Na primeira rodada (01h22) as seis colunas saíram como "coparticipação: total"; com o código de 01h38 (`leitor/condicoes.py` foi alterado entre as duas), só a coluna parcial do 484.248/19-1 recebe condição, e errada ("total"), e as outras cinco ficam sem condição. Nos dois casos, o mesmo registro aparece em duas colunas com preços diferentes sem nada que as distinga (484.252/19-9, 0 a 18: R$ 207,06 na total e R$ 260,46 na parcial). Em `corpe_hapvida_pme_am_2026-02-24.pdf`, p. 2, a coluna parcial do 484.248/19-1 sai sem condição de coparticipação; as da p. 3 saem certas.
2. Sem LLM, a acomodação não é conferida. Em `safe_hapvida_adesao_rj_2026-03.pdf`, p. 2, "SMART 400 APARTAMENTO" usa 474.464/15-1, que a ANS registra como acomodação coletiva, e na p. 3 "SMART 900 ENFERMARIA" usa 476.794/16-2, que a ANS registra como individual; nenhum alerta. Em `leitor/conferencia.py`, `regras.atributos` recebe a acomodação só do produto lido pelo LLM.
3. O leitor não compara a operadora citada no documento com a dos produtos: a capa da Safe cita 36.825-3 (Hapvida) e os 260 preços são de produtos da 359017, sem achado.
4. Na Safe, p. 2 e p. 3, as duas tabelas de cada página dizem "COPARTICIPAÇÃO TOTAL" (erro do PDF; a segunda, mais cara, deve ser a parcial). O leitor segue o rótulo, e nada avisa que há dois preços para o mesmo registro e a mesma condição.

## Na ANS

Índice local, pda-008 de 30/09/2026. HAPVIDA ASSISTENCIA MEDICA S.A., CNPJ 63.554.067/0001-98, Medicina de Grupo, sede no CE, ativa.

| Situação | Total | Coletivo empresarial | Coletivo por adesão | Individual ou familiar | Combinados |
|---|---|---|---|---|---|
| Ativo | 2.671 | 1.801 | 506 | 364 | 0 |
| Suspenso | 1.429 | 472 | 289 | 668 | 0 |
| Cancelado | 980 | 497 | 226 | 210 | 47 |
| Total | 5.080 | 2.770 | 1.021 | 1.242 | 47 |

- Ativos com nota técnica de preço: 2.399. Dos 272 sem nota, 256 são odontológicos.
- Ativos registrados em 2025: 545; em 2026: 58. Um dia concentra 686 suspensões (21/11/2023).
- Ativos por fator moderador: sem 1.123, coparticipação 802, franquia e coparticipação 686, franquia 60. Por abrangência: grupo de municípios 1.590, municipal 625, nacional 228, grupo de estados 187, estadual 41.
- A marca Hapvida cobre seis registros ativos: 368253 (Hapvida), 359017 (NotreDame Intermédica, "Hapvida NotreDame SP/RJ"), 348520 (NotreDame MG, "Hapvida Minas Gerais"), 392804 (Centro Clínico Gaúcho, "Hapvida Rio Grande do Sul"), 340782 (Clinipam, "Hapvida Clinipam Paraná") e 350249 (H.B. Saúde, "Hapvida São José do Rio Preto"). A linha "Nosso Plano" existe nos seis, então o nome do produto não identifica a operadora; só o registro identifica.

## Lacunas e próximo passo

1. **CORPe**: feito. O tipo `api_json` lê a API e trouxe as 53 tabelas Hapvida com versão.
2. **Affix**: o arquivo da web só tem o que guardou; a última cópia é de 07/06/2026. Para a versão vigente, pedir à Affix uma página ou feed dos manuais, ou receber por e-mail.
3. **Atribuição pelo registro**: as tabelas "Hapvida NotreDame" de SP e RJ são da 359017 (conferido na tabela da Safe RJ; a tabela Allcare "Hapvida NDI PME SP", lida para a NotreDame, também é toda da 359017). As de Limeira e São José dos Campos não foram conferidas. Em MG pode ser da 348520 e no RS da 392804. O cotador deve tomar a operadora do registro de cada produto, não da capa.
4. **Hapvida direto**: só por e-mail ao corretor credenciado ou parceria (Planium). O modelo de `caixa_email` está pronto, desligado.
5. **Não verifiquei**: as tabelas de SP da Safe e as de MG (limite de três amostras); os registros das tabelas CCG (RS); UFs sem material público achado (ES, MS, MT, TO, RO, AC, AP, RR; no PR a marca é a Clinipam, outro registro).
