# NotreDame Intermédica (ANS 359017)

Levantamento de 01/10/2026. Slug: `notredame_intermedica`. Só o registro 359017; Hapvida (368253) e NotreDame Intermédica Minas Gerais (348520) ficam de fora.

> **Depois deste levantamento**, o que ele apontou no leitor e no coletor foi corrigido no código, cada caso com teste (`docs/proposta.md`, seção 7):
> - o coletor passou a interpretar o robots.txt como manda a RFC 9309, com curinga. Os endereços que o site veda (`/*?version=*`, `/web*`, `/-/*`) agora são recusados;
> - o dígito desenhado à parte ("1" + "18,07") volta para o número. Os 735 preços que perdiam a centena na Super Simples e na NotreLife saem certos.

## Resumo

A tabela atual, com registro ANS, chega pela Allcare. A página pública de materiais da administradora lista as tabelas "Hapvida NDI" de SP e RJ: PME SP de 09/2026, PME RJ de 08/2026, adesão RJ de 06/2026 e adesão SP de 07/2026. A captura da Allcare que já existe no projeto pega essas tabelas sem configuração nova. O site da operadora (gndi.com.br, área do corretor) publica tabelas oficiais, agora com registro ANS impresso, mas as que estão no ar valem para contratos de junho a agosto de 2025. Rota recomendada: a Allcare (já ativa) para o preço vigente; o endereço fixo das tabelas oficiais (ativado aqui) para saber quando a operadora trocar o arquivo; e a caixa de e-mail para o material que a operadora manda ao corretor.

**Divergências a apontar no radar**

- **Tabela oficial vencida no ar.** Em 01/10/2026, a página `/corretor-pme` oferece a "Tabela de Preços - Super Simples 2 a 29 vidas", válida "para contratos assinados de 01/07/2025 a 31/08/2025". A página `/corretor-individual` oferece a NotreLife válida de 01/06 a 30/06/2025. Os arquivos foram postos em 04/09/2025 e não mudaram desde então.
- **O layout oficial mudou.** As tabelas do acervo (2023-03, 2024-01 e 2024-07) não têm registro ANS, e por isso a fonte existente diz que exigem mapeamento de coluna para produto. As de 2025 trazem registro ANS e código interno em cada coluna.
- **"Hapvida NDI" mistura registros.** Na Allcare, as tabelas de SP e RJ são da 359017. A de adesão de Minas Gerais (`tabela_adesao_ndi_bh.pdf`) tem 15 registros, todos da 348520.
- **Regras da ANS nas amostras, sem erro de leitura.**
  - Na tabela oficial, o Smart 200 UP passa por 0,3 ponto o limite do art. 3º, II, da RN 563.
  - Na Allcare de 09/2026, dois preços de 0–18 anos ficam abaixo do mínimo da nota técnica.
  - Os detalhes estão em "Amostras e leitura".

## Canais verificados

| Canal | Endereço | O que tem | robots.txt / termos | Situação |
|---|---|---|---|---|
| Área do corretor PME (site novo) | https://www.gndi.com.br/corretor-pme | PDFs em `/documents/5787792/...`: Super Simples 1 vida e 2 a 29 vidas, reembolso saúde PME, manual do corretor, guia de comunicações, condições e franquia odontológicas | Permite a página e `/documents/`. Os links levam `?version=1.1&t=...`, e o robots.txt proíbe `Disallow: /*?version=*`. O mesmo documento sem a query é permitido | Público; tabelas de jul–ago/2025 |
| Área do corretor individual | https://www.gndi.com.br/corretor-individual | Tabela de Preços NotreLife Individual Familiar, manual do portal individual | Idem | Público; tabela de jun/2025 |
| Área do corretor empresarial | https://www.gndi.com.br/corretor-empresarial | Tabela de abrangência, folder de rede SP e RJ, manuais e calendário de comissões; nenhuma tabela de preço | Idem | Público, sem preço |
| Site antigo | https://www2.gndi.com.br/documents/... | Tabelas de 2023 e 2024 (três estão no acervo), NotreLife 2023, tabelas de Minas | Permite `/documents/` | Público, defasado |
| Allcare: página de materiais | https://www.corretorallcare.com.br/materiais-de-vendas | "Hapvida NDI": PME SP (`..._ndi_sp_28_09_2026.pdf`), PME RJ (`..._ndi_rio_janeiro_rj_07_08_2026.pdf`), adesão SP e Flamengo SP (21/07/2026), adesão RJ e Flamengo RJ, adesão MG (BH e AFECOM, da 348520) e termos de redução de carência | Permite | Público e atual. A captura `pagina_publica` da Allcare (ativa) já lista os 8 PDFs |
| Qualicorp | https://tabelasdevendas.qualicorp.com.br/ | — | robots.txt responde 403 | Não acessado |
| Portal do corretor | https://gndi.my.site.com/corretor/s/login/, https://corretor.intermedica.com.br/ | Simulador e material de venda | Login | Restrito |
| Arquivo da web | API CDX do web.archive.org | 5 tabelas de 2023–2024 do site antigo (NotreLife, PF Pleno, NotreLife RJ, Web 1 vida e 2 vidas). As três do acervo não foram arquivadas | O robots.txt do arquivo responde 404; o do site permite o original | Captura configurada, inativa |
| E-mail | apoio.corretor@intermedica.com.br, no Manual do Corretor publicado em `/corretor-pme` | Recebe propostas; nenhum endereço de envio de tabela encontrado | — | Modelo de caixa inativo com `@intermedica.com.br` |

Termos de uso: o site comercial não traz termos. O endereço de termos do RI (`ri.gndi.com.br/termos-de-uso/`) abre a página de RI da Hapvida. Nenhuma cláusula contra automação apareceu.

Não usados: sites de corretoras e comparadores com "tabela NotreDame 2026" (notredameintermedicaplanos.com.br, facaseuplanodesaude, martinezcorretora e outros), porque não são canal oficial.

Pedidos feitos: 27 a www.gndi.com.br, 3 a www2.gndi.com.br e 14 à Allcare (somando a Amil), contando as leituras de robots.txt.

## Captura configurada

Arquivo: `fontes/operadoras/notredame_intermedica.json`. Acrescenta capturas à fonte existente "NotreDame Intermédica" (mesmo nome e tipo; o carregador junta).

- `url_direta`, **ativa**: os três endereços das tabelas da área do corretor, sem `?version=...&t=...`.
  - Os três: Super Simples 2 a 29 vidas, Super Simples 1 vida e NotreLife Individual Familiar.
  - O Liferay serve a versão mais nova do documento no mesmo endereço. Com download condicional (Last-Modified), a coleta percebe quando a operadora sobe outra versão.
  - O robots.txt permite esses endereços. Descoberta ao vivo: 3 candidatos.
- `pagina_publica`, **inativas**: `/corretor-pme` (2 candidatos) e `/corretor-individual` (1 candidato), com `titulo: "title"` e filtro em "Tabela de Preços".
  - Ficam inativas porque os links descobertos levam `?version=1.1&t=...`, que o robots.txt proíbe (`Disallow: /*?version=*`).
  - São a única forma de achar uma tabela nova publicada com outro UUID.
- `wayback`, **inativa**: prefixo `https://www2.gndi.com.br/documents/` desde 2023, filtrado em "Tabela de preços/PME/PF/valores" e "Tabela NotreLife".
  - Descoberta ao vivo: 5 cópias. A consulta devolve 2.700 linhas, abaixo do limite de 5.000, e cobre também `www.gndi.com.br`, porque o arquivo da web normaliza o subdomínio.
- `caixa_email`, **inativa** (modelo): servidor e usuário de exemplo, senha em `COLETA_EMAIL_SENHA`, remetente `@intermedica.com.br`.
- **Allcare**: nada novo. O filtro `/arquivos/(pdf/)?tabelas/.*\.pdf$` da captura existente já pega as tabelas NDI.

`python -m coletor.fontes` valida sem problemas.

## Amostras e leitura

Pasta `amostras/operadoras/notredame_intermedica/` (origem e hash em `manifest.json`). Leitura geométrica, sem LLM.

| Arquivo | Origem | Páginas | Preços lidos | Colunas (com registro ANS) | Confirmados pelo cálculo | Para revisão | Erros | Alertas |
|---|---|---|---|---|---|---|---|---|
| `gndi_super_simples_pme_sp_2025-07.pdf` | gndi.com.br, `/corretor-pme` | 27 | 2.707 | 278 (275) | 2.391 | 1.105 | 141 | 1.005 |
| `gndi_notrelife_individual_sp_2025-06.pdf` | gndi.com.br, `/corretor-individual` | 18 | 946 | 97 (49) | 806 | 936 | 140 | 352 |
| `allcare_ndi_pme_sp_2026-09-28.pdf` | Allcare, página de materiais | 12 | 200 | 20 (20) | 200 | 42 | 0 | 6 |

Os 47 registros distintos lidos nas três amostras são da 359017 e estão ativos. Dois também aparecem como "Transferido" de operadoras incorporadas (006980 e 328391).

O que saiu de cada uma:

- **Allcare PME SP (09/2026).** Leitura correta: os 200 valores batem com o PDF e cada coluna tem o registro certo. Os 6 alertas são achados reais, não erros de leitura:
  - Smart 200 Capital, 0–18: R$ 103,43, abaixo do mínimo da nota técnica de 03/07/2025 (R$ 105,53).
  - Smart 150 ABC, 0–18: R$ 111,80, abaixo do mínimo da nota de 06/01/2025 (R$ 114,79).
  - Quatro colunas de coparticipação parcial (Smart 200 GRU-Mogi, Alto Tietê, ABC e Sorocaba): 31% a 51% acima do VCM de notas com menos de um ano.
- **Super Simples (oficial, 2025).** Muitos valores vêm partidos na camada de texto (ver problema 1); fora deles, a grade, os registros e as faixas foram lidos.
  - 138 dos 141 erros e boa parte dos alertas de nota técnica vêm desse defeito: "variação negativa", "59+ custa 10× a faixa 0–18", preço abaixo da despesa assistencial. Nenhum valor errado passou sem revisão.
  - Os outros 3 erros são um achado real, na mesma coluna repetida nas páginas 1, 10 e 13: Smart 200 UP (486.514/20-6), sem valor partido.
  - Nessa coluna, a variação da 7ª para a 10ª faixa (R$ 321,91 → R$ 788,98, +145,1%) passa a da 1ª para a 7ª (R$ 131,51 → R$ 321,91, +144,8%). Isso contraria o art. 3º, II, da RN 563, por 0,3 ponto.
- **NotreLife (oficial, 2025).** Tem o mesmo defeito, em proporção maior. Além disso, cada produto tem duas colunas de preço ("Médica ¹" e "Médica + ROL") sob um único registro centralizado, e metade das colunas ficou sem registro.

Problemas do leitor (código central):

1. **Primeiro dígito em palavra separada.** Atinge as tabelas oficiais da GNDI, geradas por "Microsoft: Print To PDF" a partir do Excel.
   - Na camada de texto, o primeiro dígito de muitos valores vem numa palavra à parte, encostada no resto: "R$ 1 18,07", "R$ 2 23,69", "R$ 1 .401,77".
   - A leitura geométrica (`leitor/geometrico.py`) pega só o pedaço que casa com `RE_MOEDA`. Assim, 118,07 vira 18,07 e 223,69 vira 23,69. Com o milhar partido ("1" + ".401,77"), o valor não é lido.
   - O caminho de OCR tem uma etapa que junta pedaços de valor colados (`_juntar_moeda` em `leitor/ocr.py`); a leitura geométrica não tem equivalente.
   - `gndi_super_simples_pme_sp_2025-07.pdf`: 460 valores partidos no PDF; 357 lidos sem o primeiro dígito, em 43 colunas, nas páginas 1, 2, 4, 7, 8, 10, 11, 13, 19, 20, 22, 25 e 26.
   - `gndi_notrelife_individual_sp_2025-06.pdf`: 595 valores partidos; 378 lidos sem o primeiro dígito, em 50 colunas, nas páginas 1, 3, 5, 7, 9, 11, 13, 15 e 17.
   - Nenhum desses valores passou sem revisão: as regras da ANS pegaram todas as colunas. Mesmo assim, o cálculo pelo padrão de faixas marcou como "confirmado" 45 valores errados na Super Simples e 294 na NotreLife. Colunas irmãs com o mesmo erro se confirmam entre si.
2. **Registro ANS centralizado sobre duas colunas.** `gndi_notrelife_individual_sp_2025-06.pdf`, páginas ímpares de 1 a 17. O registro fica numa célula mesclada sobre "Médica ¹" e "Médica + ROL", e só uma das duas colunas recebe o registro: 48 das 97 colunas ficaram "sem registro ANS".
3. **Rótulo e condição da coluna.**
   - Nas tabelas oficiais, o título espaçado letra a letra ("C O M C O P A R T I C I P A Ç Ã O P A R C I A L") entra no rótulo das colunas: "C O M AMBULATORIAL NOSSO", "L S O T O T A L * P A Ç Ã O P".
   - Na Allcare, páginas 5 e 6, o rótulo puxa texto de fora da grade ("CE - ANS. - A partir Smart 200 GRU - Mog").
   - Também na Allcare, a condição "região: capital" foi aplicada às 10 colunas de cada grade porque uma delas se chama "Smart 200 Capital". Isso pesa no casamento de versões por condição de venda.

## Na ANS

Índice local (`dados/ans/indice.sqlite`, pda-008 de 30/09/2026). Operadora 359017: NOTRE DAME INTERMÉDICA SAÚDE S.A., CNPJ 44.649.812/0001-38, nome fantasia HAPVIDA NOTREDAME SP/RJ, medicina de grupo, SP, ativa.

| Situação | Coletivo empresarial | Coletivo por adesão | Individual ou familiar | Empresarial + adesão | Total |
|---|---|---|---|---|---|
| Ativo | 1.057 | 183 | 73 | 0 | 1.313 |
| Suspenso | 591 | 248 | 543 | 0 | 1.382 |
| Cancelado | 608 | 204 | 329 | 2 | 1.143 |
| Total | 2.256 | 635 | 945 | 2 | 3.838 |

- Dos 1.313 ativos, 287 são odontológicos. Ficam 1.026 planos médicos ativos: 836 empresariais, 132 de adesão e 58 individuais.
- 1.014 ativos têm nota técnica (VCM por faixa); a mais recente é de 14/09/2026.
- Fator moderador dos ativos: 632 sem, 377 com franquia e coparticipação, 295 com coparticipação e 9 com franquia.
- 98 planos passaram a "Suspenso" em 2026.

## Lacunas e próximo passo

- **Ativar a descoberta na página do corretor.** O robots.txt já é lido com curinga, e a página fica bloqueada como o site pede. Para usá-la, o tipo `pagina_publica` precisaria tirar a query `?version=...&t=...` do link (endereço canônico do Liferay) antes de baixar.
- **Tabela oficial atual.** O site da operadora não tem tabela de 2026. Se a GNDI publicar com outro UUID, só a descoberta na página acha. Até lá, a Allcare cobre SP e RJ, e a caixa de e-mail (modelo com `@intermedica.com.br`) cobre o que chega ao corretor.
- **Leitor.** O dígito solto já volta ao valor. Falta herdar o registro ANS da célula mesclada sobre duas colunas (NotreLife); até lá, essas colunas vão para revisão.
- **Arquivo da web.** O histórico está incompleto: as três tabelas do acervo não foram arquivadas.
- **Outras administradoras.** O levantamento da Hapvida (`fontes/operadoras/hapvida.json`) ativou a página da Safe com tabelas "Hapvida" de adesão RJ e SP (`safeadmin.com.br/produtos/hapvida/`). No cadastro da ANS, SP e RJ são da 359017, então essas tabelas devem ser desta operadora. Essas tabelas não foram abertas; vale conferir os registros para atribuir a fonte à operadora certa.
- **Não verificado:**
  - a tabela Super Simples 1 vida (só HEAD: 996 KB, Last-Modified 04/09/2025);
  - as tabelas Allcare que não viraram amostra. Da adesão SP (versão 07.2026, 21 registros) e da adesão RJ (versão 06.2026, 14 registros) só os registros foram conferidos, todos da 359017 e ativos, sem rodar o leitor;
  - Flamengo SP, Flamengo RJ, PME RJ e AFECOM (MG), que não foram abertas;
  - se `@gndi.com.br` também é remetente de tabelas;
  - o portal do corretor, que exige login.
