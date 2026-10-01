# Detalhes técnicos

Complemento da proposta (`docs/proposta.md`). A proposta conta o raciocínio; aqui ficam as medições, as regras e as tabelas que sustentam cada número, para quem quiser conferir. Todos os números se refazem com `scripts/medir_acervo.py`, `scripts/medir_calculo.py` e os testes (`./verificar.sh`).

## 1. Obtenção dos dados

### 1.1 Fontes em camadas

A ordem é da mais confiável e com menos risco para a menos confiável e com mais risco:

| # | Fonte | O que dá | Como entra | Situação |
|---|---|---|---|---|
| 1 | **Dados abertos da ANS** | Catálogo dos 28,9 mil planos ativos (registro, contratação, acomodação, coparticipação, reembolso, abrangência, situação); **preço de referência por plano e faixa etária, com banda legal**; rede hospitalar por plano; pedidos de mudança de rede, com a data em que valem; operadoras canceladas; reajustes | Download automático: catálogo diário, rede mensal | Implementado: catálogo, operadoras, preço de referência, rede hospitalar e mudanças de rede (seção 3.6) |
| 2 | **Materiais públicos** de operadoras e administradoras | Tabela de venda em PDF: preço por faixa, registro ANS, coparticipação, carências, vigência | Coletor que observa páginas, endereços fixos e APIs abertas e baixa só o que mudou; o arquivo da web traz as versões antigas | Implementado (seção 1.5): Allcare, CORPe, Safe, Sinpro-DF e as condições comerciais de Bradesco e SulAmérica, entre 18 fontes configuradas |
| 3 | **Materiais recebidos** pela equipe (e-mail, WhatsApp, portal) | O mesmo tipo de tabela, de fontes restritas | Upload na tela e caixa de e-mail dedicada, lida só para leitura e só de remetente autenticado | Implementados; o e-mail é o canal das 6 operadoras que não publicam preço (seção 1.3) |
| 4 | **Sites públicos das operadoras** | Condições comerciais (coparticipação, reembolso, portfólio); rede não hospitalar | Mesmo coletor, por configuração | Condições implementadas; a rede hospitalar vem da ANS, que é a fonte oficial |
| 5 | **Parcerias** (administradoras, plataformas como a Planium, APIs de operadoras) | Tabela estruturada na origem | Feed ou API | Proposta comercial |
| 6 | **Credencial do corretor** (robô com o login dele) | Material de portal restrito | Só com consentimento, escopo mínimo e sem dados de clientes | Ponte futura; não é por onde começar |

### 1.2 Acesso: o que pode, o que não pode

- **Rede credenciada é pública por lei.** A RN ANS 486/2022 obriga a operadora a publicar a rede de cada plano, "atualizada em tempo real", e proíbe restringir esse acesso a beneficiários. É a base para coletar rede de páginas públicas.
- **Regras de coleta:**
  - sem login;
  - sem contornar captcha ou WAF;
  - respeitando robots.txt (lido como manda a RFC 9309, com curinga) e termos de uso;
  - robots.txt que não responde ou nega acesso vale como "não": na dúvida, o robô não entra;
  - volume baixo, com o robô identificado.
- **Onde os termos proíbem, o caminho é parceria.** Amil, Unimed (guia nacional) e Porto se enquadram nisso.
- **LGPD:** coletar só prestador pessoa jurídica. Nome e CRM de médico são dado pessoal e ficam de fora.
- **Nunca coletar de outro cotador.** Os casos de condenação por concorrência desleal no Brasil (Catho, Webmotors) são exatamente de extração de base de concorrente.

### 1.3 Mapa das operadoras do Cotador

As 9 operadoras citadas na página do Cotador foram mapeadas uma a uma, sem login e obedecendo o robots.txt. Cada uma tem um relatório em `docs/operadoras/` (canais, linha do robots.txt, termos, amostras lidas, números da ANS) e a configuração das capturas em `fontes/operadoras/`.

| Operadora (ANS) | Preço vigente público | Por onde o preço chega | Captura configurada |
|---|---|---|---|
| Bradesco Saúde (005711) | não: só no Portal de Negócios, com login | material do comercial ao corretor | endereço fixo para coparticipação e portfólios; e-mail (modelo) |
| SulAmérica (006246) | não; a última pública é de 10/2023 | Qualicorp, que bloqueia robôs (o robots.txt responde 403) | páginas e endereços fixos de condições, coparticipação e reembolso; e-mail (modelo) |
| Amil (326305) | não: o Kit Corretor gera o PDF de preço na hora, por formulário | Kit Corretor; os termos vedam automação | todas inativas, à espera de autorização; e-mail (modelo) |
| NotreDame Intermédica (359017) | sim, pela Allcare (SP e RJ, 06 a 09/2026); a oficial no ar venceu em 2025 | Allcare | Allcare (já ativa) e endereço fixo das tabelas oficiais |
| Hapvida (368253) | não própria; sim pelas administradoras | Allcare (43 tabelas em 15 UFs), CORPe (53), Affix, Safe | Allcare; API da CORPe (tipo novo); página da Safe; Affix pelo arquivo da web |
| Central Nacional Unimed (339679) | lista pública, mas os PDFs ficam num servidor cujo robots.txt não responde (504) | e-mail ou parceria | página oficial pronta e desligada até o robots.txt responder |
| Smile Saúde (395480) | não | canal fechado (WhatsApp, portal); só uma tabela de 2023 na Allcare | e-mail (modelo); arquivo da web da tabela de 2023 |
| Quallity Pró Saúde (418170) | só a do Sinpro-DF, impressa "vigente 08/2022" | administradora Platinum | página do Sinpro-DF; e-mail (modelo) |
| Saúde Sim (320111) | **operadora extinta**: registro cancelado em 2022, falência em 2023 | nenhum | nenhuma; o radar avisa que o registro foi cancelado na ANS |

O que o mapa mostra:
- **Nenhuma das 9 publica a tabela vigente aberta no próprio site.** O preço chega pelas administradoras (Allcare, CORPe, Affix, Safe, Qualicorp) ou por canal fechado (portal com login, e-mail, WhatsApp). Por isso o desenho tem quatro entradas: página pública e API das administradoras, e-mail para o que chega fechado, upload, e parceria para escala.
- **Uma marca, vários registros.**
  - "Hapvida" cobre seis registros na ANS, e as tabelas "Hapvida NotreDame" de SP e RJ trazem produtos da NotreDame (359017) mesmo quando a capa cita a Hapvida.
  - A SulAmérica vende também pela Paraná Clínicas (416428, 141 planos novos em 2026, contra 12 no registro principal), e a Bradesco pelo 421715.
  - O radar acompanha o grupo, sempre pelo registro do produto.
- **Divergências que o mapeamento achou:**
  - a tabela "Ana Costa" que o Kit Corretor da Amil publica é de outra operadora do grupo (360244), cancelada por incorporação em 06/2026, com os planos agora suspensos;
  - a NotreDame mantém no ar tabela oficial vencida em 2025;
  - a Quallity anuncia preço abaixo do piso da nota técnica e mostra como ativos 7 planos que a ANS suspendeu em 09/2026;
  - a Smile anuncia produto "DF" sem nenhum plano DF ativo na ANS;
  - a Saúde Sim, extinta, ainda aparece na página do Cotador.
- **O que o mapeamento ensinou ao código.** Cada caso virou correção no leitor ou no coletor, com teste (seção 3.5):
  - layout que o leitor não conhecia;
  - robots.txt com curinga;
  - API sem tipo de captura.

### 1.4 Quando a fonte está indisponível ou é restrita

Mesmo sem acesso ao material, a ANS avisa **que algo mudou**. O sistema transforma esses sinais em pedidos dirigidos: "pedir à operadora X a tabela nova do plano Y". Não é preciso varrer tudo às cegas.

| Sinal na ANS | O que significa para o Cotador |
|---|---|
| Nova nota técnica registrada depois da tabela vigente | Tabela nova a caminho (visto na SulAmérica/Qualicorp: notas de 25/08/2026 acima da tabela de junho) |
| Plano passou para "comercialização suspensa" | Parar de cotar |
| Exclusão de hospital deferida, com data futura | Avisar o corretor antes de a mudança valer (implementado, seção 3.6) |
| Reajuste anual do pool de PME publicado | Prever a próxima tabela da operadora |
| Operadora cancelada | Bloquear |

Os corretores assinantes também são fonte. Eles recebem tabelas de supervisores e administradoras que a equipe não recebe. Um botão "enviar tabela" com crédito para quem colabora aumenta a cobertura. A dupla leitura e a ANS conferem esse material antes de publicar.

### 1.5 O coletor: fonte é quem publica, captura é por onde chega

O coletor segue a mesma lógica do leitor: o motor é genérico, e uma fonte nova não pede código.

- **Fonte e captura são coisas diferentes.** A Allcare é uma fonte; a página de materiais dela e o histórico no arquivo da web são duas capturas da mesma fonte. A Unimed Guarulhos bloqueia robôs no site, então a captura que funciona é a caixa de e-mail. Cada fonte tem quantas capturas precisar, e o material de todas cai nas mesmas séries.
- **O motor faz, para qualquer captura:**
  - lê o robots.txt e obedece;
  - identifica o robô e espaça os pedidos;
  - baixa só o que mudou (ETag, Last-Modified e hash);
  - confere se o PDF abre antes de registrar;
  - liga a versão nova à anterior pela URL sem a data;
  - registra cada coleta e manda ler o material novo;
  - avisa quando a fonte quebra, como uma página que listava tabelas e passou a listar nenhuma.
- **Tipos de captura:** cada um é uma classe pequena que só descobre candidatos. São cinco hoje:

| Tipo | O que faz | Cuidado embutido |
|---|---|---|
| Página pública com links | acha os PDFs de tabela na página da fonte | leitura tolerante de HTML: o parser da biblioteca padrão parava na tag 181 da página da Allcare |
| Endereço fixo | baixa o PDF quando ele muda | GET condicional: sem mudança, nada é baixado |
| API pública em JSON | lê a lista de tabelas que a página da fonte monta por JavaScript (a CORPe é o caso) | filtro por título e endereço, e a data da versão tirada do nome do arquivo |
| Histórico no arquivo da web | lista na API CDX da Wayback as versões que a fonte já tirou do ar e baixa cada uma uma vez | o robots.txt do site original também vale para a cópia: o arquivo não serve para contornar a recusa da fonte |
| Caixa de e-mail (IMAP) | lê os PDFs anexados, soltos ou em .zip | só leitura (nada é marcado como lido ou apagado); só remetente da lista e autenticado (DKIM ou DMARC registrados pelo servidor da caixa), porque o campo From se falsifica com facilidade; a senha fica numa variável de ambiente |

- **Fonte nova de um tipo que já existe** é um arquivo JSON em `fontes/`, validado antes de entrar (tipo, campos obrigatórios, expressões). É o equivalente a mapear um layout novo no leitor.

Na prática:

| Captura | Resultado |
|---|---|
| Allcare, página pública | 96 tabelas encontradas: 84 novas, baixadas e lidas sozinhas em 3 minutos; 10 reconhecidas pelo hash, porque já estavam no acervo; 2 links quebrados (404) na própria página da Allcare. Na segunda passada, 94 "sem mudança" sem baixar nada |
| Allcare, histórico no arquivo da web | 17 versões antigas das tabelas acompanhadas: 9 entraram no histórico, com 91 tabelas e dupla leitura (US$ 0,07); 3 já estavam no acervo; 5 vieram truncadas pelo próprio arquivo da web (todas as cópias de maio de 2024 pararam em 1 MiB, sem o fim do PDF) e ficaram marcadas como defeituosas, sem gerar documento |
| Unimed Guarulhos, endereço fixo | **bloqueada**: o robots.txt proíbe /site/documents/, onde fica a tabela |
| Unimed Guarulhos, e-mail (simulado) | de três mensagens, entrou só a da operadora autenticada, com a tabela dentro de um .zip. A de remetente igual sem autenticação e a de outro domínio foram ignoradas. A segunda leitura da caixa não traz nada de novo, porque a captura guarda o último e-mail lido |
| Qualicorp, endereço fixo | **bloqueada**: o servidor nega o acesso ao próprio robots.txt, e na dúvida o coletor não entra |
| CORPe, API pública (tabelas Hapvida) | 53 tabelas, cada uma com a data da versão. Teste às cegas: 3.241 preços; os 3.000 da leitura geométrica todos confirmados, 0 divergências, 86,4% sem revisão, US$ 0,31. Os 241 preços que só o LLM leu são o adicional de odonto, preço único que vem ao lado da tabela e vai para revisão |

**Teste às cegas.** As 84 tabelas novas da Allcare nunca tinham passado pelo leitor. Foram coletadas e lidas sem mudar uma linha de código:

| Medida | Resultado |
|---|---|
| Preços da leitura geométrica | 8.553, **todos confirmados pelo LLM**, com 0 divergências |
| PDFs com preço lido pela geométrica | 83 de 84; o que falta tem preço único, sem faixa etária (a geométrica não tem âncora; o LLM leu os 6 preços, que foram para revisão) |
| Sem revisão (produto identificado) | 73,9%; o resto vem sobretudo das regras da ANS (nota técnica, banda), e nenhum preço foi para revisão por divergência entre as leituras |
| Custo da segunda leitura | US$ 0,56 pelas 84 (cerca de US$ 0,007 por PDF) |

Três achados no caminho, todos com teste:
- **robots.txt da Unimed.** O leitor de robots.txt da biblioteca padrão do Python liberava o site inteiro. O arquivo começa com "User-agent: *" seguido de uma linha em branco, e o parser descarta as regras que vêm depois. Um coletor que confiasse nele teria baixado justamente o que a Unimed pede para não baixar. O coletor interpreta o arquivo como manda a RFC 9309.
- **Concorrência.** Ler 84 documentos em paralelo revelou que o índice da ANS usava uma conexão SQLite compartilhada entre threads, e dois documentos lidos ao mesmo tempo quebravam o segundo. Agora cada thread tem a sua conexão.
- **Versão antiga chegando depois.** Uma cópia de 2024 baixada hoje teria substituído o preço de 2026 na cotação. Agora o material mais antigo que outro já recebido da mesma série entra no histórico, na posição da sua data, e nunca vira o preço vigente (seção 3.2).

---

## 2. Redução do trabalho manual

### 2.1 O fluxo

```
recebe o PDF ─► identifica (hash, fonte, série) ─► lê duas vezes ─► identifica o produto pelo registro ANS
     ─► confere (entre leituras + regras da ANS) ─► pessoa revisa só o apontado ─► publica nova versão ─► avisa o que mudou
```

- **Leitura 1: geométrica.** Acha os rótulos das faixas da ANS ("0 a 18", "00-18", "59 ou +"...), pega os valores à direita e associa cada coluna ao registro ANS impresso acima dela, pela posição. É determinística, gratuita e aponta a coordenada exata de cada número. PDF sem texto (escaneado, foto, print) passa antes por OCR local.
- **Leitura 2: LLM** (GPT-6 Luna por padrão; Gemini e Claude entram por configuração). Cada página vai como um PDF de uma página só, em paralelo: o provedor extrai o texto e vê a imagem da página. A saída é estruturada e validada. Entende a estrutura do documento: produtos, condição de cada tabela, coparticipação, carências, elegibilidade, vigência. Também diz quando o preço embute outro produto, como odonto.
- **Conferência 3: cálculo.** A ANS exige que o contrato fixe o percentual de aumento em cada mudança de faixa, e as operadoras aplicam os mesmos percentuais a uma linha inteira de produtos. Deixando uma faixa de lado, as colunas que batem com esta em todas as outras dizem quanto ela deveria valer, ao centavo. É aritmética sobre a própria tabela, independente das duas leituras e da ANS: desempata a divergência e confirma o preço que só uma leitura pegou.
- **Por que duas leituras?** É a **dupla digitação** que já se usa para conferir cadastro manual, só que automática. Os dois leitores erram de formas diferentes. Quando concordam, a confiança é alta; quando discordam, a célula vai para uma pessoa. O LLM nunca publica sozinho.
- **O produto é identificado pelo registro ANS**, nunca pelo nome: há 344 nomes repetidos numa mesma operadora. Com o registro, o catálogo da ANS preenche sozinho contratação, acomodação, coparticipação e abrangência.

### 2.2 O que é automático e onde entra uma pessoa

| Automático | Pessoa |
|---|---|
| Ler preços, identificar produto, preencher atributos | Conferir as células apontadas, com o PDF ao lado e o número destacado |
| Validar contra as regras da ANS | Aprovar, corrigir ou ignorar uma coluna |
| Comparar com a versão anterior e com outras fontes | Ligar coluna a produto quando o PDF não traz registro ANS. É feito uma vez por layout; a NotreDame é o caso real |
| Gerar os avisos (reajuste, produto retirado, divergência, suspensão, vigência) | Decidir a publicação (um clique) |
| Detectar tabela nova na página da administradora | Negociar parcerias e acessos |

### 2.3 Resultados no acervo real

| Medida | Resultado |
|---|---|
| PDFs e layouts | 25 reais, de 8 fontes (Allcare, CORPe, Affix, Qualicorp, Safe, Unimed Guarulhos, Unimed FERJ e NotreDame), cada uma com seu layout: cabeçalho transposto, tabelas lado a lado, cabeçalho quebrado em duas linhas, texto girado; mais 1 escaneado simulado |
| Preços extraídos | 10.573 (só o que aparece na página desenhada: texto escondido no PDF é descartado) |
| Sem revisão humana, só com a leitura geométrica | **80,1%** dos preços de produtos identificados (3.614 de 4.513) no acervo completo (`scripts/medir_acervo.py` refaz a conta) |
| Apontados para revisão | 899, nenhum por divergência de leitura. Regras da nota técnica (726, dos quais 714 em duas tabelas que a regra questiona inteiras: Unimed Vitória abaixo da despesa assistencial, 440; Affix SAMP fora da banda com nota recente, 274); plano suspenso (40); registro inexistente ou plano cancelado (70); coluna com faixa faltando, que vai inteira para revisão (44); regras de faixa da RN 563 (19). A pessoa decide uma dezena de casos, um por tabela, e não 899 células |
| PDF escaneado (inclinado, borrado, com sujeira) | 352 de 360 preços lidos, **0 errados**; os 8 faltantes vão para revisão |
| Tempo | segundos por PDF com texto; cerca de 10 s por página com OCR |

**A segunda leitura, medida no acervo inteiro.** Os dois modelos baratos mais recentes, com o mesmo método (página por página, raciocínio baixo):

| Medida | GPT-6 Luna (OpenAI) | Gemini 3.8 Flash (Google) |
|---|---|---|
| Preços da leitura geométrica confirmados | **10.570 de 10.573** | **10.571 de 10.573** |
| Divergências em PDF com texto | 0 | 0 |
| PDF escaneado, contra o original | 357 de 360 certos | 358 de 360 certos |
| Carências e regras de coparticipação lidas | 276 e 739 | 201 e 750 |
| Custo do acervo (26 PDFs, 362 páginas) | **US$ 0,35** (cerca de US$ 0,001 por página) | US$ 1,65 |
| Tempo somado | 598 s | 347 s |

- **Divergências:** só no escaneado (3 no Luna, 2 no Gemini). Em todas, o OCR estava certo, e as células foram para revisão. Nos 8 preços que o OCR não leu, os dois modelos acertaram todos.
- **Registro ANS divergente entre as leituras:** nenhum. O LLM confirma também qual coluna é qual produto.
- **Preços que só o LLM leu:** preços avulsos, como adicional de odonto, "a partir de" e promoção. Não são tabela por faixa, e nenhum deles é publicado sem uma pessoa, porque só se publica coluna com todas as faixas.
- **Escolha:** GPT-6 Luna como padrão. Mesma qualidade por um quinto do custo. O provedor troca por configuração.

Quatro lições de rodar com dados reais:
- **A dupla leitura achou um erro da leitura geométrica.** Um PDF da NotreDame carrega uma coluna de preços copiada e escondida na borda de duas grades: está no arquivo, mas não aparece na página. A leitura geométrica lia essa coluna; os dois LLMs, que veem a página, não. Agora o leitor confere cada palavra contra a página desenhada e descarta o que ninguém vê (20 preços fantasmas; nenhum preço visível afetado).
- **Página por página.** Com o documento inteiro numa chamada, o modelo resumia os PDFs grandes e avisava que tinha pulado tabelas: confirmava só 28% dos preços. Lendo cada página separada, em paralelo, a confirmação foi a quase 100%, e o custo subiu pouco mais da metade.
- **Modelo barato para tudo, o forte para o difícil.** No escaneado, o GPT-6.1 Sol acertou 360 de 360 preços (US$ 0,105, 18 vezes o Luna). As poucas diferenças dos modelos baratos já caem em revisão pela divergência com o OCR. Por isso o modelo forte só se paga em PDF escaneado ou para desempatar página com divergência.
- **A dupla leitura aumenta a confiança; a automação muda pouco.** O percentual sem revisão foi de 80,1% com uma leitura para 81,1% com duas e o cálculo, porque o LLM completa faixas que a leitura geométrica perdeu e o cálculo desempata as divergências. O que manda preço para revisão neste acervo são sobretudo as regras da ANS (plano suspenso, nota técnica nova); dos 899 apontados com uma leitura, só 44 vêm de faixa que a leitura não achou, e nenhum de divergência entre as leituras. O ganho é que quase todo preço tem confirmação independente, e cada discordância aponta a célula exata.

---

## 3. Confiabilidade e atualização

### 3.1 Regras com base legal, testadas nos dados

| Regra | O que pega | Exemplo real |
|---|---|---|
| **RN 563/2022** (faixas: 59+ até 6× a 0–18; variação da 7ª à 10ª faixa ≤ da 1ª à 7ª; sem queda) | Dígito trocado, faixas trocadas, coluna mal associada | A validação acusou na hora um defeito do próprio leitor, que deslocava as faixas |
| **Padrão de faixas da própria tabela** (os percentuais fixados em contrato, RN 563) | Preço que não segue o percentual das colunas iguais no resto; recalcula o valor ao centavo | No escaneado, recalculou exatamente os 3 dígitos que o LLM errou: 474,77, 892,23 e 767,05 |
| **Nota técnica do plano (RN 564/2022)**, com a nota plausível para a data do material | Faixa que foge da proporção das outras em relação ao preço de referência, que é o sinal típico de erro de digitação; preço abaixo da despesa assistencial (vedado) | Unimed Guarulhos: R$ 116,56 contra o piso de R$ 122,77 na faixa 0–18 do Essencial III |
| **Nota técnica nova depois do material** | A operadora registrou preço novo na ANS depois da tabela que está publicada: existe tabela nova, mesmo sem acesso a ela | Qualicorp/SulAmérica: 11 planos com nota de 25/08/2026, depois do material de junho; Affix/Hapvida: 3 planos com nota de 07/2026, depois do material de 08/2025 |
| **Situação na ANS (RN 543/2022)** | Plano suspenso ou cancelado sendo vendido | Rio Preto (abr/2026): 2 planos suspensos desde 11/2024 ainda na tabela |
| **Catálogo ANS** | Registro inexistente | Safe: 476.696/16-4 não existe |
| **Cadastro de operadoras** | Operadora cancelada | Saúde Sim |
| **Lei 9.656/98 art. 12** | Carência acima do máximo legal | (lida pelo LLM) |

Três cuidados para não gerar alarme falso, todos vindos dos dados reais:

1. **Arredondamento.** As operadoras usam o limite exato das regras, então é preciso tolerância de centavos.
2. **Reajuste uniforme não é erro.** Quando todas as faixas sobem na mesma proporção, a nota técnica é que está velha, e isso vira informação, não alerta.
3. **Preço composto.** Quando o preço inclui odonto, as regras de proporção não se aplicam ao total. O leitor percebe isso pelo cabeçalho ("+ ODONTO") ou pelo LLM.

### 3.2 Origem, vigência e histórico

- **Origem de cada preço:** documento, com hash, fonte e URL; página; posição na página, que a tela destaca; forma de leitura; quem aprovou.
- **Versões:** nada é sobrescrito. Cada publicação é uma versão nova, com vigência e ligada ao documento de onde saiu, e a anterior vira histórico.
- **Material antigo nunca volta a ser o preço.** Se chega um material mais antigo que outro já recebido da mesma série (cópia do arquivo da web, PDF velho reenviado), cada tabela entra no histórico do produto na posição da sua data, e a vigente não muda, em qualquer ordem que os documentos cheguem. Versão antiga não altera a cotação, então entra sozinha, sem esperar revisão. Foi assim que o histórico da Allcare se montou: Unimed Fortaleza com +24,4% da versão de agosto de 2024 para a seguinte, Unimed BH com +18,2% da de junho de 2024.
- **Comparação pelo registro ANS e pela condição de venda, não pela posição.** Na Rio Preto, de abril para maio as 14 colunas trocaram de lugar com os mesmos preços. Um diff por posição acusaria 14 mudanças; o sistema diz, corretamente, "nenhuma". Na versão de agosto, detectou os 2 produtos retirados. Na Unimed BH (2024 → 2026), mediu o reajuste: +18,46%. Na Qualicorp, quando a operadora juntou duas composições familiares numa tabela só, o sistema comparou cada composição com a mesma composição e avisou que a condição mudou (seção 3.5).

### 3.3 Divergências e dado desatualizado

- **Entre fontes.** A mesma tabela Hapvida DF adesão está na Allcare, na CORPe e na Affix. Allcare e CORPe batem centavo a centavo; a Affix está **9,7% abaixo**, com a tabela de 2025. O radar avisa. Na cotação, o corretor vê a tabela antiga marcada ("material de 08/2025"), com o aviso de que outra fonte tem o mesmo produto 10,7% mais caro com material de 09/2026.
- **Idade do dado.** Toda cotação mostra a data do material de origem e quando foi confirmado pela última vez. Uma tabela nova com os mesmos preços reconfirma a anterior.
- **Vigência.** A tabela da Unimed FERJ venceu em 30/09/2026, e o radar pede a versão nova.
- **Sinais da ANS** (seção 1.4): nota técnica nova, suspensão, cancelamento, exclusão de hospital com data futura.

### 3.4 Calcular para conferir

Em 88 das 115 tabelas com 3 ou mais colunas, todas as colunas usam o mesmo percentual de aumento entre faixas. O mesmo padrão se repete nas várias tabelas de um documento (1 vida, 2 a 29, 30 a 99 vidas). Isso permite recalcular cada preço:

| Medida | Resultado |
|---|---|
| Preços que o cálculo refaz (com 2 ou mais colunas iguais no resto) | 88% (8.989 de 10.189 preços de colunas com 7 ou mais faixas lidas) |
| Erro de digitação plantado de propósito (dígito trocado ou invertido, 1.434 casos, sorteio com semente fixa) | apontado em 100% dos erros acima de 1%, 100% dos de 0,1% a 1% e 93% dos de centavos; o valor original volta ao centavo em 91%, 91% e 79% dos casos (`scripts/medir_calculo.py`) |
| Escaneado, com dupla leitura | as 3 divergências e os 8 preços que só o LLM leu foram confirmados pelo cálculo: de 12 células para revisão, sobrou 1 (o preço abaixo do piso da ANS, que é achado real) |
| Escaneado, só com OCR | as faixas que o OCR perdeu vêm com o valor calculado (24-28: R$ 645,28, exato) |
| Alarme falso no acervo limpo | nenhum; desvios de até R$ 0,10 são arredondamento da planilha da operadora e não viram alerta |

A regra para não errar pelo outro lado: o cálculo só confirma um preço quando bate com uma das leituras até o centavo. Valor calculado que discorda vira alerta com sugestão, nunca correção automática.

### 3.5 Onde um preço pode ir para o lugar errado

Na página real da Unimed Guarulhos, as trocas que um layout novo pode causar na leitura geométrica foram provocadas de propósito:

| Troca provocada | O que pega |
|---|---|
| **Produto trocado:** o registro de uma coluna vai para outra | Com a dupla leitura, as duas colunas levam erro "registro diverge entre leituras". Só com a geométrica, a regra da ANS pega uma delas (preços 31% acima da referência do plano errado) |
| **Faixa deslocada:** os preços caem uma linha abaixo | Com a dupla leitura, todas as 228 células vão para revisão. Só com a geométrica, a referência da ANS por faixa acusa 84 células e a faixa 59+ fica faltando |
| **Condição trocada entre versões:** as mesmas tabelas (1 vida, 2 a 29, 30 a 99 vidas) em outra ordem | Nada pegava: 33 "reajustes" falsos |

O terceiro caso era um buraco real, e acontecia no próprio acervo. Na Qualicorp (2024 → 2026), a comparação por posição casava "Titular + 1 dependente" com "Titular + 2 ou mais", e o radar mostrava "reajustes" de −21% a +15% no mesmo produto.

A correção: cada grade tem uma **condição de venda**, lida do título e do rótulo por um vocabulário fechado (vidas, coparticipação, adesão, composição familiar, região, porte, grupo). Versões e fontes são casadas pela condição; a posição só desempata; duas condições que se contradizem nunca são casadas. Com isso, a reordenação não gera nenhum reajuste, e a Qualicorp mostra o que de fato aconteceu: 26 tabelas com preço alterado (mediana −10,8%), 13 condições encerradas (a operadora juntou "titular" e "titular + 1" numa tabela só) e 4 produtos que saíram.

O mesmo teste achou um segundo defeito: o alerta de faixa faltando não marcava nada para revisão, porque a faixa que falta não tem célula. Agora a coluna inteira vai para revisão: eram colunas incompletas passando como resolvidas. As simulações viraram testes automatizados.

**O que o mapeamento das 9 operadoras e o teste às cegas da CORPe ensinaram.** Layout novo é onde um leitor genérico pode errar. Os agentes que mapearam as operadoras trouxeram 9 casos reais, e a coleta da CORPe trouxe mais 2. Cada um virou correção no código central, com o PDF real num teste:

| Caso real | O que acontecia | Correção |
|---|---|---|
| NotreDame: o primeiro dígito desenhado à parte ("1" e "18,07" encostados) | 735 preços perdiam a centena (118,07 virava 18,07). O cálculo "confirmava" 339 deles, porque o erro se repetia igual em várias colunas | o dígito encostado volta para o número |
| CNU: duas tabelas de anos diferentes em camadas, uma sob o fundo das células | o texto das duas se misturava letra a letra, e a leitura dava 0 preços | sai a camada coberta, pela ordem de desenho, só em página com camadas de texto empilhadas: 520 preços lidos |
| Smile: "Com coparticipação" e "Sem coparticipação" escritos na vertical ao lado das grades | as grades ficavam sem condição | o texto girado ao lado da grade vira condição; das duas ordens de leitura, vale a que forma uma condição conhecida |
| Smile, CNU e Amil: "&gt; 59 anos", "Acima 59 anos", "59" com o "ou +" na linha de baixo | a última faixa se perdia | rótulos aceitos |
| SulAmérica 2023 comparada com a nota técnica de 2026 | 112 alertas falsos de "abaixo da despesa" | o preço é comparado com as notas plausíveis para a data do material, de 1 ano antes a 6 meses depois, porque a data na ANS é a do registro; o alerta só fica se nenhuma delas explica o preço |
| Affix: "com coparticipação total ou parcial" na capa | a grade inteira virava "total" | enumeração de opções não define condição, e "com coparticipação" é compatível com parcial e total |
| Guia de coparticipação e manual de vendas | saíam com 0 preços, sem aviso | aviso de "nenhuma tabela de preço encontrada" |
| NotreDame: `Disallow: /*?version=*` no robots.txt | o parser da biblioteca padrão do Python ignora curinga e liberava o endereço | o robots.txt é interpretado como manda a RFC 9309: curinga, regra mais longa vence, grupo do próprio robô |
| CORPe: tabelas servidas por uma API JSON, com a página montada em JavaScript | nenhum tipo de captura lia JSON | tipo de captura novo, de 40 linhas: 53 tabelas Hapvida, cada uma com a data da versão |
| CORPe: endereço do PDF com espaço ("TABELA HAPVIDA_ANAPOLIS_V.1.pdf") | o pedido falhava em 50 das 53 tabelas | o endereço é pedido como o navegador pede, com o espaço codificado |
| CORPe, Hapvida BH: negrito falso, com cada letra desenhada duas vezes no mesmo lugar ("0000--1188") | a segunda grade da página ficava ilegível | sai a cópia idêntica da letra (mesma letra, fonte e posição) |

Nenhuma dessas correções mudou a leitura do acervo de demonstração (10.573 preços antes e depois). Elas ampliam o que o leitor entende sem quebrar o que já entendia, e o teste do acervo inteiro é o que garante isso a cada mudança.

### 3.6 Rede, reembolso e coparticipação: o registro oficial ao lado do material

O material de venda traz o preço. Rede, reembolso e coparticipação também pesam na escolha do corretor, e o material traz pouco ou de forma desigual. A ANS registra os três para cada produto, e os dados são abertos:

- **Reembolso, coparticipação, acomodação e abrangência** vêm do registro do produto (livre escolha, fator moderador). A cotação mostra os quatro ao lado do preço, e o leitor já confere o material contra eles: tabela que diz "sem coparticipação" num produto registrado com coparticipação vira alerta.
- **Rede hospitalar por plano.** A ANS publica a rede de cada produto num zip de 1,4 GB, dividido por UF. O sistema baixa por HTTP Range só o trecho de cada UF, descompacta em fluxo e guarda só os planos acompanhados. Para os 392 planos do acervo: 82.888 vínculos de hospital em todas as UFs, em 5,6 minutos, num arquivo de 14 MB. Na cotação, o corretor escolhe a UF do cliente e vê quantos hospitais o plano tem ali, quantos com pronto-socorro, e a lista.
- **Mudanças de rede antes de valerem.** A operadora precisa pedir à ANS para tirar um hospital da rede, e a ANS publica cada pedido com o resultado e a data em que vale. Nos planos do acervo, foram 838 pedidos em 2025 e 2026. Os deferidos viram aviso no radar e na cotação:

| Exemplo real | O que o corretor vê |
|---|---|
| Natal Hospital Center, nos planos Essencial Flex da Unimed Natal | "sai em 26/10/2026; no lugar entram Casa de Saúde São Lucas e Hospital Unimed (substituição deferida pela ANS)" |
| Hospital Mogiano (Mogi das Cruzes/SP) | saiu da rede de 9 planos publicados em 20/07/2026, sem substituto: alerta no radar |
| Plano municipal da Hapvida cotado para um cliente no RN | "nenhum hospital da rede em RN na ANS" |

Nenhum desses fatos está no PDF de venda. Todos vêm do registro oficial, com data e protocolo.

### 3.7 Determinismo e auditoria

Uma cotação precisa poder ser explicada meses depois: de onde veio cada preço e por que ele foi publicado.

- **O que é determinístico:** leitura geométrica, OCR, cálculo pelo padrão de faixas, regras da ANS, condição de venda, casamento de versões, histórico e captura. O mesmo PDF dá sempre o mesmo resultado, e um teste lê o mesmo material duas vezes e compara o resultado byte a byte.
- **O que não é:** a leitura por LLM. Por isso ela nunca decide sozinha. Concorda com a outra leitura ou com o cálculo, ou a célula vai para uma pessoa. E cada leitura fica gravada pelo hash do PDF, com modelo, data e custo, então a conferência refeita com a gravação dá o mesmo resultado (também testado).
- **O que fica registrado:**
  - o PDF original, nunca apagado, com hash, fonte e URL;
  - cada coleta, com o que achou, baixou, ignorou e por quê;
  - cada versão publicada, com o documento e a coluna de onde saiu;
  - cada evento do radar, com a regra e o dado que o geraram.

---

## 4. Estrutura técnica

```
 FONTES                        CAPTURA                    LEITURA E CONFERÊNCIA                    PUBLICAÇÃO
 ANS (dados abertos) ────────► jobs diário e mensal ──► índice ANS + rede hospitalar ───────┐
 páginas públicas ──► página ─┐                                                              ▼
 endereços fixos ───► URL ────┤
 APIs públicas ─────► JSON ───┤                                                                  
 arquivo da web ────► Wayback ┼─► motor ─► arquivo original ─► leitor geométrico/OCR ─┐
 e-mail da equipe ──► IMAP ───┤  (robots,  (hash, fonte,       leitor LLM ──────────────┼─► conferência ─► revisão ─► tabela publicada ─► API do Cotador
 upload / parceria ─► API ────┘   delta)    série, data)                               │   (regras ANS,   (tela)    (versão, vigência,   selo de origem,
                                                                                         │    cálculo)                histórico)           rede e reembolso
                                                                                         └──────────────────────────► radar de eventos ◄──────┘
```

| Componente | No protótipo | Em produção | Por quê |
|---|---|---|---|
| Aplicação e API | Django + DRF | igual | ORM, admin e migrações prontos; a equipe mantém sem mágica |
| Interface | React + Vite + Tailwind | igual | a tela de revisão (PDF + destaques + grade) exige interação rica |
| Banco | PostgreSQL | PostgreSQL | versões, eventos e JSON na mesma base; transação na publicação |
| Arquivos originais | disco local | armazenamento de objetos (S3 ou equivalente) | o PDF é a prova da origem; nunca se apaga |
| Índice ANS | SQLite local (319 MB, montado em 21 s) | tabelas no Postgres, atualizadas por job diário | consulta por registro em milissegundos |
| Leitor geométrico | pdfplumber (texto e coordenadas) | igual | exato, grátis e explicável |
| OCR | RapidOCR (modelos ONNX, local) | igual, ou serviço de OCR em nuvem | sem custo por página e sem mandar documento para fora |
| LLM | GPT-6 Luna (OpenAI) por padrão; Gemini 3.8 Flash e Claude por configuração. Página por página, saída estruturada (pydantic) | igual, com cache por hash; modelo forte (GPT-6.1 Sol) só para escaneado ou divergência | lê qualquer layout novo sem código; o acervo inteiro custou US$ 0,35 |
| Coleta | pacote `coletor` com cinco tipos de captura; fontes em `fontes/*.json`; agendador diário no docker compose (perfil `coleta`) | igual, agendado por captura (Celery beat) | fonte nova é configuração; o motor cuida de robots.txt, intervalo, download condicional, validação do PDF e histórico |
| Rede hospitalar | SQLite local montado dos dados abertos da ANS por HTTP Range (14 MB para 392 planos) | tabelas no PostgreSQL, atualizadas por job mensal | o zip oficial tem 1,4 GB; baixar e guardar só o necessário |
| Processamento | thread em segundo plano | fila (Celery ou RQ + Redis) | o documento é a unidade de trabalho; os leitores não guardam estado, então escala horizontalmente |
| Publicação | EC2 `t3.small` na AWS com Docker Compose, atrás de um túnel da Cloudflare (`deploy/subir-com-tunel.sh`) | domínio próprio, com túnel nomeado ou balanceador; banco gerenciado | nenhuma porta aberta no servidor e HTTPS sem configurar domínio |

**Crescimento para mais operadoras e planos:**
- **Operadora nova em PDF:** não exige código. O leitor é genérico e já cobre os layouts das 8 fontes do acervo.
- **Fonte nova de material:** se é de um tipo que já existe (página com links, endereço fixo), é configuração. Um tipo novo (API de parceiro, SFTP) é uma classe que só descobre candidatos; o resto é do motor.
- **Rede por site:** exige um conector por operadora, no mesmo contrato do coletor, com o mesmo aviso de quebra.
- **Dados grandes da ANS** (rede hospitalar, com cerca de 19 GB): processados por UF, extraídos do ZIP oficial com HTTP Range, sem baixar tudo.
- **Custo do LLM:** cerca de US$ 0,001 por página com o GPT-6 Luna. Mil PDFs de 15 páginas por mês custariam uns US$ 15. Documento repetido não é relido (hash). O modelo forte, 18 vezes mais caro, entra só onde o barato não basta: PDF escaneado e página com divergência.

---

## 5. Riscos e limitações

| Risco | Mitigação |
|---|---|
| Layout novo ou esquisito | O LLM lê sem código; a divergência entre leituras vai para uma pessoa; a regra da ANS pega associação errada |
| PDF sem registro ANS (ex.: NotreDame) | Mapeamento coluna → produto feito uma vez por layout e reaproveitado |
| Preço de venda vigente não é público | Continua dependendo de material e de parcerias; o sistema reduz a digitação e o erro, não a relação com as operadoras |
| Termos de uso e captcha | Não contornar; buscar parceria. As regras de coleta ficam registradas por fonte |
| Erro ou custo do LLM | Ele nunca publica sozinho; custo medido (US$ 0,001 por página); cache por hash; o provedor troca por configuração |
| Modelo pequeno resume documento longo | Leitura página por página: a confirmação foi de 28% para quase 100% |
| Mudança de formato nos dados da ANS | Validação na carga (colunas, contagens) e alerta de job quebrado |
| Página da fonte muda de formato | O coletor avisa quando a página que listava tabelas passa a listar nenhuma ("coleta com problema" no radar) |
| Fonte muda o nome do arquivo ou a pasta entre versões | A versão nova vira série nova e o histórico se parte; o próximo passo é reconhecer a série pelo conjunto de registros ANS do documento |
| Material antigo chegando depois do atual (arquivo da web, PDF reenviado) | Entra no histórico na posição da sua data e nunca volta a ser o preço vigente (seção 3.2) |
| LGPD | Só prestador PJ; nenhum dado de beneficiário |
