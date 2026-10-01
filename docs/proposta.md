# Radar do Cotador: tabelas obtidas, conferidas e atualizadas sem digitação

**Gustavo Henrique** · desafio técnico do Cotador de Planos de Saúde · outubro de 2026

## Resumo

Hoje cada tabela que chega ao Cotador é lida e digitada à mão, plano por plano. O Radar do Cotador troca a digitação por conferência. O sistema busca o material onde ele é publicado ou recebe o que chega por e-mail, lê cada tabela de dois jeitos independentes, confere com os dados oficiais da ANS e chama uma pessoa só para o que não fecha. Cada preço publicado guarda de onde veio, e o sistema avisa quando algo muda, antes de o corretor errar. Quando a ANS indica que uma tabela mudou e o material não está à mão, o sistema diz a qual operadora pedir qual tabela.

O protótipo roda com material público real:

- **81,1% dos preços de produtos identificados pelo registro ANS passam sem revisão humana.** No acervo, esses produtos respondem por menos da metade dos 10.573 preços lidos (4.513 com uma leitura); os demais vêm de PDFs sem o registro e ficam fora da conta. O que sobra para revisão vem quase todo das regras da ANS sobre o preço ou o plano, concentrado em poucas tabelas.
- Em dois testes às cegas, com 137 tabelas que o leitor nunca tinha visto, todo preço da primeira leitura foi confirmado pela segunda, sem nenhuma divergência.
- As 9 operadoras da página do Cotador foram mapeadas uma a uma. Nenhuma publica a tabela vigente aberta no próprio site. NotreDame e Hapvida chegam pelas administradoras que publicam as tabelas, e o sistema coleta sozinho. Seis só entregam por canal fechado ou não aceitam robô: para cada uma, a seção 3 diz qual acesso falta.
- O sistema e o mapeamento acharam problemas que estavam passando: uma operadora extinta desde 2022 ainda listada na página do Cotador, planos suspensos na ANS em tabela de venda, uma tabela 9,7% mais barata porque era a versão antiga e um hospital que saiu da rede de 9 planos publicados.
- A segunda leitura sai por cerca de US$ 0,001 por página. O acervo inteiro custou US$ 0,35.

O protótipo sobe com `docker compose up`, e o roteiro da demonstração está em `docs/roteiro-demo.md`. A versão completa, com o back-end, está publicada na AWS (endereço no `README.md`). Sem instalar nada, dá para abrir também a versão estática no navegador, em [gustavohenriquers.github.io/radar-cotador](https://gustavohenriquers.github.io/radar-cotador/), ver o [resumo em vídeo de 41 s](https://gustavohenriquers.github.io/radar-cotador/video/radar-cotador-motion.mp4), a [demonstração completa](https://gustavohenriquers.github.io/radar-cotador/video/radar-cotador-demo.mp4), de 1 min 36 s, ou passar pelos [slides](https://gustavohenriquers.github.io/radar-cotador/pdf/slides.pdf).

| Pedido do desafio | Onde está |
|---|---|
| O problema, as premissas e o escopo | seções 1 e 2 |
| Obtenção dos dados, acessos, fontes indisponíveis ou restritas | seção 3 e `docs/operadoras/` |
| Redução do trabalho manual: o que é automático e quando entra uma pessoa | seção 4 |
| Confiabilidade e atualização: conferência, divergências, origem, vigência, histórico | seção 5 |
| Estrutura técnica: componentes, fluxo, armazenamento, crescimento | seção 6 |
| Plano de implementação: primeira entrega, etapas, riscos, dependências, medição | seção 7 |
| Os desafios que apareceram no caminho e como foram resolvidos | seção 8 |
| Protótipo: o que é real e o que é simulado | seção 9 e `README.md` |

---

## 1. O problema

O desafio descreve dois problemas que se alimentam. O acesso é limitado: parte do material fica em portal restrito ou depende de contato interno, e o que está no sistema pode divergir das condições vigentes. A atualização é manual: cada informação precisa ser lida e cadastrada, plano por plano, com retrabalho, erro de digitação e atraso. Quanto mais difícil é conseguir o material, mais tarde ele é digitado, e mais tempo o dado velho fica no ar. Na ponta, o corretor recebe uma cotação que pode estar desatualizada e não tem como saber de onde veio o número.

A pesquisa trouxe três fatos que guiaram a proposta:

- O dado muda o tempo todo. Só em 2026, um concorrente publicou pelo menos 225 avisos de mudança de tabela, em 106 dias diferentes. Com digitação, o dado chega atrasado.
- Ninguém tem API de preço. Os concorrentes mantêm as tabelas com "mesa técnica" ou leem PDF com IA, e as APIs que as operadoras têm são de pós-venda, só para parceiros. Ler PDF com IA já é comum; falta conferir cada número e mostrar de onde ele veio.
- A desatualização já aparece hoje. A página do Cotador lista a Saúde Sim, que teve o registro cancelado pela ANS em 2022 e a falência decretada em 2023. Uma checagem automática contra a ANS pegaria isso no primeiro dia.

O corretor precisa de um preço certo e atual, e de saber de onde ele veio.

## 2. Premissas e escopo

Premissas:

- O dado é o preço por faixa etária de cada produto, identificado pelo registro ANS, em cada condição de venda (vidas, coparticipação, região, composição familiar). Ao lado dele vêm rede, reembolso, coparticipação e carências.
- O material que a equipe já recebe por e-mail, WhatsApp ou portal pode ir para uma caixa dedicada ou ser subido numa tela.
- A ANS segue publicando os dados abertos que o sistema usa. A carga confere o formato, porque ele muda de vez em quando.
- Usar um modelo de linguagem como segunda leitura é aceitável, com custo medido e sem publicar nada sozinho.

O protótipo se concentra no que trava o processo hoje: obter, ler, conferir e atualizar o preço. Ficaram de fora, de propósito:

- entrar em portal com login sem autorização da operadora ou do corretor dono da conta;
- a rede de clínicas e laboratórios, que a ANS não publica e que pede um coletor por operadora;
- o motor de cotação. A cotação do protótipo existe para mostrar o dado chegando na ponta, e o Cotador já tem a sua.

---

## 3. Obtenção dos dados

### A ANS como base

A ANS publica de graça, nos dados abertos, uma base que nenhum material de venda tem:

- o catálogo de planos, com contratação, acomodação, coparticipação, reembolso e situação de cada um;
- o preço de referência de cada plano por faixa etária, com a faixa de variação permitida;
- a rede hospitalar de cada plano;
- os pedidos de mudança de rede, com a data em que valem.

Com ela, o sistema confere cada tabela de venda e percebe mudanças mesmo sem o material na mão.

### O mapa das 9 operadoras

As operadoras da página do Cotador foram mapeadas uma a uma por agentes de IA trabalhando em paralelo, com revisão humana de cada achado. Cada uma tem um relatório em `docs/operadoras/`, com canais, robots.txt, termos de uso e amostras lidas. Nenhuma publica a tabela vigente aberta no próprio site. O preço chega de três jeitos:

| Como o preço chega | Operadoras | O que o sistema faz |
|---|---|---|
| Administradoras que publicam as tabelas | NotreDame e Hapvida, pela Allcare, CORPe, Affix e Safe | coleta sozinho todo dia e baixa só o que mudou |
| Canal fechado ou fonte que não aceita robô | Bradesco, SulAmérica, Amil, CNU, Smile e Quallity | aceita upload na tela; a caixa de e-mail de cada uma está configurada, mas desligada (tabela abaixo) |
| Nenhum: operadora extinta | Saúde Sim | o radar avisa que o registro foi cancelado na ANS |

### O acesso que falta em cada operadora fechada

| Operadora | Onde está o preço hoje | O que destrava |
|---|---|---|
| Bradesco | só no Portal de Negócios, com login, e no material que o comercial manda ao corretor | caixa de e-mail que receba esse material; parceria para escala. Coparticipação e portfólios já são coletados de endereço fixo |
| SulAmérica | na Qualicorp, que bloqueia robôs (o robots.txt responde 403); a última tabela pública é de 10/2023 | caixa de e-mail para o material do comercial e parceria com a Qualicorp. Condições, coparticipação e reembolso já são coletados |
| Amil | no Kit Corretor, que gera o PDF na hora, por formulário; os termos vedam automação | autorização ou parceria com a Amil; até lá, e-mail ou upload do PDF que o corretor gera no Kit. As capturas estão prontas e inativas |
| CNU | lista pública, mas os PDFs ficam num servidor cujo robots.txt não responde (504) | a captura da página oficial está pronta e desligada até o robots.txt responder; até lá, e-mail ou parceria |
| Smile | canal fechado (WhatsApp, portal) | caixa de e-mail que receba o material da Smile, só de remetente autenticado, ou parceria |
| Quallity | só a tabela do Sinpro-DF, impressa "vigente 08/2022"; o preço passa pela administradora Platinum, e o portal do corretor exige login | caixa de e-mail que receba as tabelas da Quallity e da Platinum, ou parceria com a Platinum |

A caixa de e-mail aceita só remetente autenticado (DKIM ou DMARC), porque o remetente se falsifica fácil. Até aqui, ela só passou pelo fluxo com mensagens simuladas da Unimed Guarulhos. Para as seis operadoras acima, a caixa é um modelo desligado: só traz preço quando a equipe do Cotador apontar para ela o material que já recebe.

### Respeito à fonte

- Sem login e sem contornar captcha.
- robots.txt obedecido e lido do jeito certo (seção 8, caso 5). Na dúvida, o robô não entra.
- Robô identificado e volume baixo.
- Onde os termos de uso proíbem robôs, como na Amil, o caminho é a parceria.
- Da rede, só prestador pessoa jurídica, por causa da LGPD.
- Nunca coletar de outro cotador.

### Quando a fonte está fechada

Mesmo sem o material, a ANS indica que algo mudou. O protótipo já gera estes avisos:

- uma nota técnica registrada depois da tabela publicada indica tabela nova a caminho;
- um hospital com saída deferida vira aviso ao corretor antes de a mudança valer;
- um plano suspenso vira alerta, e os preços dele vão para revisão.

Cada sinal vira um pedido dirigido, do tipo "pedir à operadora X a tabela nova do plano Y". O que a operadora mandar entra pela caixa de e-mail ou pelo upload e segue o fluxo de qualquer tabela.

---

## 4. Redução do trabalho manual

O fluxo é o mesmo, venha o material de onde vier:

```
recebe o PDF → lê duas vezes → identifica o produto pelo registro ANS → confere
  → uma pessoa olha só o que não fechou → publica uma versão nova → avisa o que mudou
```

### Um preço do começo ao fim

A tabela PME 2026 da Unimed Guarulhos mostra o caminho inteiro. O robots.txt do site proíbe a pasta onde ela fica, e o coletor não entra (seção 8, caso 5). O canal é o e-mail: na simulação, de três mensagens, entrou só a da operadora autenticada, com a tabela dentro de um .zip. O sistema lê 360 preços e aponta 1: a faixa 0–18 do Essencial III, R$ 116,56, abaixo do piso de R$ 122,77 da nota técnica que a própria operadora registrou na ANS. A pessoa abre o PDF com a célula destacada e decide se aprova ou corrige. É aqui que ela entra, e só aqui. Na versão escaneada do mesmo PDF, o OCR leu 352 de 360 preços, sem nenhum errado, e achou o mesmo problema.

### Duas leituras independentes

- A primeira é geométrica. Acha os rótulos das faixas etárias e pega os valores pela posição na página. PDF escaneado passa antes por OCR.
- A segunda é de um modelo de linguagem, que lê cada página e entende a estrutura da tabela: produtos, condições, coparticipação, carências e vigência.

É a dupla digitação que já se usa para conferir cadastro manual, só que automática. Os dois leitores erram de jeitos diferentes. Quando concordam, a confiança é alta; quando discordam, aquela célula vai para uma pessoa. O modelo de linguagem nunca publica nada sozinho.

### Uma terceira conferência, por cálculo

A ANS exige que o contrato fixe o percentual de aumento entre as faixas etárias, e as operadoras usam os mesmos percentuais em toda uma linha de produtos. Então dá para recalcular cada preço a partir das outras colunas da própria tabela, ao centavo. Isso desempata quando as leituras discordam e pega dígito trocado. Num teste com 1.434 erros de digitação plantados de propósito, o cálculo apontou todos os erros acima de 0,1% e 93% dos de centavos. O valor calculado aparece para a pessoa como sugestão, nunca como correção automática. O cálculo tem um limite, visto na seção 8, caso 7: erro que se repete igual em várias colunas passa por ele.

### O produto pelo registro na ANS

Há 344 nomes de plano repetidos dentro de uma mesma operadora, então o produto é identificado pelo registro, e com ele o catálogo da ANS completa o resto. Quando o PDF não traz o registro, como os da NotreDame, a proposta é uma pessoa ligar cada coluna ao produto uma vez por layout, e o sistema reaproveitar essa ligação nas versões seguintes. O protótipo conta esses preços à parte, como "sem produto identificado", e eles ficam fora dos percentuais de automação abaixo.

### O que é automático e o que fica com uma pessoa

| Automático | Com uma pessoa |
|---|---|
| Ler os preços, identificar o produto, preencher os atributos | Conferir as células apontadas, com o PDF ao lado e o número destacado |
| Conferir contra a ANS, contra a outra leitura e pelo cálculo | Aprovar, corrigir ou ignorar uma coluna |
| Comparar com a versão anterior e com outras fontes | Ligar coluna a produto quando o PDF não traz o registro ANS |
| Avisar o que mudou | Decidir a publicação, com um clique, e negociar acessos e parcerias |

### Resultados

No acervo de teste:

- 10.573 preços, de 25 PDFs reais de 8 fontes, cada uma com um layout diferente, e de 1 escaneado simulado. Com uma leitura, 80,1% dos 4.513 preços de produtos identificados pelo registro ANS passam sem revisão; com as duas leituras e o cálculo, 81,1%.
- Dos 899 preços apontados com uma leitura, quase todos vêm das regras da ANS: 726 da nota técnica (714 deles em duas tabelas que a regra questiona inteiras), 70 de registros que não existem ou de planos cancelados, 40 de planos suspensos e 19 das regras de faixa da RN 563. Os outros 44 são de colunas com faixa que a leitura não achou, que vão inteiras para revisão. Na prática, a pessoa decide uma dezena de casos, um por tabela.
- No PDF escaneado, os 8 preços que o OCR não leu foram lidos pela segunda leitura e confirmados pelo cálculo.

Em tabelas novas, que o leitor nunca tinha visto, trazidas pelos próprios coletores:

| Teste às cegas | Tabelas | Preços da primeira leitura confirmados | Sem revisão |
|---|---|---|---|
| CORPe | 53 | 3.000 de 3.000 | 86,4% |
| Allcare | 84 | 8.553 de 8.553 | 73,9% |

As 84 tabelas da Allcare foram coletadas e lidas sem mudar uma linha de código. A CORPe pediu um tipo de captura novo, de 40 linhas, e ajustes no coletor e no leitor (seção 8, casos 7 e 10). Na Allcare, o que foi para revisão eram sobretudo sinais da ANS, como nota técnica e banda de preço, e nenhum preço foi por divergência entre as leituras.

---

## 5. Confiabilidade e atualização

### Regras com base legal

| Regra | O que verifica |
|---|---|
| Faixas etárias (RN 563) | a última faixa não passa de 6 vezes a primeira, e nenhum preço cai com a idade |
| Preço de referência (RN 564) | o preço contra a nota técnica do plano e a faixa de variação permitida |
| Situação na ANS (RN 543) | plano suspenso, plano cancelado ou operadora cancelada sendo vendidos |
| Catálogo da ANS | registro que não existe: a Safe imprime um que não está no catálogo |
| Carências (Lei 9.656) | carência acima do máximo legal |
| Atributos | coparticipação e acomodação do material contra o registro na ANS |

Cada regra foi testada contra o acervo real antes de entrar, porque regra que acusa preço certo só atrapalha. Daí vieram a tolerância de centavos, porque as operadoras usam o limite exato, a aceitação de reajuste igual em todas as faixas, o cuidado com preço que embute odonto e a comparação com a nota técnica da época certa (seção 8, caso 8).

### Origem, versões e histórico

- Todo preço publicado guarda documento, página, posição na página, forma de leitura e quem aprovou. O PDF original nunca se apaga.
- Nada é sobrescrito. Cada publicação é uma versão nova, com vigência, e a anterior vira histórico.
- A comparação entre versões usa o produto e a condição de venda. Na tabela de Rio Preto, as 14 colunas trocaram de lugar entre abril e maio, com os mesmos preços. Uma comparação por posição acusaria 14 reajustes; o sistema diz, corretamente, que nada mudou.
- Material antigo nunca volta a ser o preço vigente. Assim o arquivo da web montou sozinho o histórico da Allcare: 9 versões antigas entraram sem mudar nenhuma cotação, e o sistema mediu, por exemplo, o reajuste de 24,4% da Unimed Fortaleza de agosto de 2024 para a versão seguinte.

### Divergências entre fontes

Quando o mesmo produto aparece com preços diferentes em fontes diferentes, o sistema avisa e diz qual material é mais novo. A mesma tabela Hapvida DF aparece na Allcare, na CORPe e na Affix. A da Affix está 9,7% abaixo porque é de 2025, e o corretor vê o alerta na cotação.

### Dado desatualizado

- Toda cotação mostra a data do material de origem e quando ele foi confirmado pela última vez.
- Nota técnica nova depois da tabela vira aviso: a SulAmérica registrou notas novas depois da tabela publicada em junho.
- Hospital saindo da rede vira aviso: o Hospital Mogiano saiu de 9 planos publicados, e o Natal Hospital Center sai da rede da Unimed Natal em 26/10.
- Ao lado do preço, a cotação mostra a rede hospitalar do plano no estado do cliente e o que o registro diz sobre reembolso e coparticipação.

### O mesmo material dá sempre o mesmo resultado

Leitura, cálculo, regras e histórico são determinísticos, e um teste lê o mesmo PDF duas vezes e compara o resultado. O modelo de linguagem é a única parte que não é. Por isso nunca decide sozinho, e cada leitura dele fica gravada: a conferência refeita meses depois chega ao mesmo número.

---

## 6. Estrutura técnica

![Fluxo do Radar do Cotador: as fontes entram pela coleta, o PDF é guardado e lido duas vezes, a conferência usa o cálculo das faixas e a ANS, uma pessoa revisa só o que não fechou, e a versão publicada alimenta a cotação e o radar. Os dados abertos da ANS ficam na base da conferência e dos avisos.](img/arquitetura.svg)

| Parte | Escolha | Por quê |
|---|---|---|
| Aplicação | Django + Django REST Framework | a stack do desafio; admin, migrações e ORM prontos |
| Interface | React | a tela de revisão, com o PDF ao lado e a célula destacada, pede interação rica |
| Banco | PostgreSQL | versões, avisos e dados semiestruturados na mesma base, com transação na publicação |
| PDFs originais | disco no protótipo; armazenamento de objetos em produção | o PDF é a prova da origem e nunca se apaga |
| Primeira leitura | pdfplumber e OCR local | exata, grátis, explicável, e o documento não sai da empresa |
| Segunda leitura | modelo de linguagem barato (GPT-6 Luna), trocável por configuração | confirmou 10.570 de 10.573 preços por US$ 0,35; o Gemini teve a mesma qualidade por quase cinco vezes o custo |
| Dados da ANS | índice local montado dos dados abertos | consulta em milissegundos; da rede, baixa só o trecho de cada estado de um arquivo de 1,4 GB |
| Coleta | um motor só e tipos de captura pequenos; as fontes ficam em arquivos de configuração | fonte nova não pede código |
| Processamento | thread no protótipo; fila em produção | o documento é a unidade de trabalho, e os leitores não guardam estado |

Para crescer em planos e operadoras:

- Operadora nova em PDF não pede código. O leitor é genérico e já entende os layouts das 8 fontes do acervo, mais os que o mapeamento trouxe.
- Tipo de captura novo é uma classe pequena. O da API pública da CORPe saiu com 40 linhas e trouxe 53 tabelas.
- Mil PDFs de 15 páginas por mês custariam uns US$ 15 de leitura, e documento repetido não é relido.

---

## 7. Plano de implementação

| Fase | Entrega | Valor |
|---|---|---|
| 1 (semanas 1 e 2) | Saúde da base atual: cruzar o que o Cotador já tem cadastrado com a ANS (operadoras canceladas, planos suspensos, registros que não existem) e mostrar a rede e o reembolso do registro oficial ao lado de cada plano | valor no primeiro dia, sem mudar o processo da equipe |
| 2 (semanas 2 a 6) | Dupla leitura, tela de revisão e publicação versionada, começando pelas administradoras que já estão configuradas e pela caixa de e-mail | a digitação vira revisão do que foi apontado |
| 3 (semanas 6 a 10) | Radar de mudanças (preço, rede, divergência, vigência, nota técnica nova), selo de origem na cotação e coleta agendada | o dado passa a avisar antes de o corretor errar |
| 4 (depois) | Parcerias com as operadoras de canal fechado e com plataformas como a Planium; envio de tabelas pelos corretores assinantes, conferidas pela dupla leitura e pela ANS antes de publicar; rede de clínicas e laboratórios | cobertura e atualização perto do tempo real |

A primeira entrega é de propósito a mais simples: não depende de nenhuma operadora, e só a checagem contra a ANS já pegaria a Saúde Sim.

### Riscos e tratamento

| Risco | Tratamento |
|---|---|
| A operadora só entrega o preço por canal fechado ou não aceita robô. É o caso de 6 das 9 (tabela da seção 3) | o sistema reduz o trabalho e o erro, mas a relação com a operadora continua necessária: caixa de e-mail e upload, depois parceria |
| Um layout que o leitor não entende | a segunda leitura cobre, a divergência vai para uma pessoa, e a correção entra no leitor genérico, sem caso especial |
| O modelo de linguagem erra ou fica caro | ele nunca publica sozinho, o custo é medido por página, e o provedor troca por configuração |
| A fonte muda de formato | o coletor avisa quando uma página que listava tabelas passa a não listar nenhuma |
| A fonte troca o nome do arquivo entre versões | o histórico se parte em dois; o próximo passo é reconhecer a tabela pelo conjunto de registros ANS que ela traz |
| LGPD | só dado de pessoa jurídica, e nenhum dado de beneficiário |

### Dependências

O que depende da equipe do Cotador para começar:

- escolher qual base do Cotador cruzar com a ANS na fase 1;
- dar acesso ao material que a equipe já recebe, ligando a caixa de e-mail de cada operadora fechada ou usando o upload na tela;
- uma chave de provedor de LLM (OpenAI, Google ou Anthropic). Sem ela, o sistema funciona com uma leitura só e todas as regras;
- o contato comercial com as operadoras, para os pedidos dirigidos e as parcerias.

### Como saber se funcionou

- Tempo até o Cotador: do material publicado pela operadora até a tabela disponível para o corretor. No protótipo, a parte automática levou 3 minutos: as 84 tabelas novas da Allcare foram baixadas e lidas sozinhas. A medida conta também a revisão do apontado e a publicação, que dependem de uma pessoa.
- Automação: a parte dos preços publicados sem revisão. A meta inicial é 75%. O protótipo chega a 81,1% no acervo e, nas tabelas novas, a 86,4% na CORPe e 73,9% na Allcare (seção 4).
- Qualidade: erros achados depois de publicar, em reclamações e correções.
- Frescor: a idade média do material por trás das cotações.
- Cobertura: operadoras e planos com tabela vigente.
- Custo por tabela processada.

---

## 8. Desafios que apareceram e como foram resolvidos

Rodar com material real trouxe problemas que nenhum desenho no papel mostraria. O mapeamento das operadoras, feito com agentes de IA, trouxe PDFs e sites diferentes de tudo o que o acervo tinha. Cada falha exposta virou correção com teste, e nenhuma correção mudou o que já funcionava: o acervo segue lendo os mesmos 10.573 preços.

1. O modelo de linguagem resumia os documentos longos. Lendo o PDF inteiro de uma vez, pulava tabelas e confirmava só 28% dos preços. Página por página, em paralelo, foi a quase 100%, e o custo subiu pouco mais da metade, ainda perto de US$ 0,001 por página.
2. Uma coluna de preços que ninguém via. Um PDF da NotreDame carregava uma coluna escondida na borda da grade. A leitura geométrica lia; os modelos, que veem a página, não. Agora o leitor descarta toda palavra que não aparece na página desenhada.
3. Reajustes que não existiam. Comparando pela posição das colunas, a Qualicorp de 2024 contra a de 2026 casava "titular + 1 dependente" com "titular + 2 ou mais" e mostrava "reajustes" de −21% a +15% no mesmo produto. A comparação passou a usar a condição de venda (vidas, coparticipação, composição familiar): reordenar colunas não gera mais reajuste nenhum, e a Qualicorp mostra o que de fato mudou, com 26 tabelas com preço novo, 13 condições encerradas e 4 produtos que saíram.
4. Coluna incompleta passando como resolvida. A faixa que falta não tem célula, então o alerta não mandava nada para revisão. Agora a coluna inteira vai.
5. O robots.txt lido errado pela biblioteca do Python. O leitor padrão liberava o site inteiro da Unimed Guarulhos, por causa de uma linha em branco, e ignorava os curingas da NotreDame. Um coletor que confiasse nele baixaria justamente o que essas fontes pedem para não baixar. O coletor passou a seguir a norma (RFC 9309), com teste para cada caso.
6. Uma versão antiga podia virar o preço do dia. Uma cópia de 2024, vinda do arquivo da web ou reenviada, substituiria o preço de 2026. Agora ela entra no histórico, na posição da sua data, em qualquer ordem que os documentos cheguem.
7. Layouts que quebravam o leitor, todos resolvidos no leitor genérico, sem caso especial:
   - dígito desenhado à parte: num PDF da NotreDame, o "1" de "118,07" era uma palavra separada, e 735 preços perdiam a centena. O cálculo chegou a confirmar parte deles, porque o erro se repetia igual em várias colunas;
   - tabelas em camadas: duas tabelas de anos diferentes sobrepostas, misturadas letra a letra;
   - negrito falso: a mesma letra desenhada duas vezes no mesmo lugar;
   - condição na vertical: "Com coparticipação" escrito girado ao lado da grade;
   - rótulos de faixa novos, como "Acima 59 anos" e "> 59".

   O teste do acervo inteiro garante que uma correção não quebra outra. Ele pegou o primeiro filtro de camadas apagando metade dos preços de uma tabela, e o filtro passou a agir só quando há camadas de texto empilhadas.
8. Alarme falso por comparar com a nota técnica errada. Uma tabela de 2023 comparada com a nota de 2026 gerava 112 alertas falsos de preço abaixo do custo. A data da nota na ANS é a do registro, que pode vir antes ou depois de a tabela valer. Agora o preço é comparado com as notas plausíveis para a época do material, e o alerta só fica quando nenhuma delas explica o preço. A nota mais nova virou aviso próprio: a tabela provavelmente está defasada.
9. Cópias com defeito no arquivo da web. Cinco versões antigas da Allcare estavam cortadas em 1 MiB no próprio arquivo. Agora o PDF é aberto antes de ser registrado, e a cópia com defeito fica marcada e não é pedida de novo.
10. Endereços que o navegador aceita e o código não. A API da CORPe devolve links com espaço, e 50 das 53 tabelas falhavam. O coletor passou a pedir o endereço como o navegador pede.
11. Leituras em paralelo derrubando umas às outras. Com 84 documentos ao mesmo tempo, o índice da ANS dividia uma única conexão. Agora cada leitura tem a sua.

Hoje são 115 testes automatizados, e um comando (`./verificar.sh`) roda todos, junto com a validação das fontes e o build da interface.

---

## 9. O protótipo: o que é real e o que é simulado

Real:

- os dados abertos da ANS, baixados do portal oficial;
- os 25 PDFs do acervo, públicos, com origem, data e hash em `amostras/manifest.json`;
- as coletas: a página de materiais da Allcare, as versões antigas no arquivo da web e as 53 tabelas da API da CORPe;
- o mapeamento das 9 operadoras, com as amostras lidas;
- a rede hospitalar e as mudanças de rede, da ANS;
- a publicação do protótipo completo numa EC2 da AWS, com acesso por um túnel da Cloudflare;
- todo o pipeline: leitura, OCR, conferência, publicação versionada, comparação de versões, radar e cotação.

Simulado:

- o PDF escaneado, gerado a partir da tabela real da Unimed Guarulhos, torto, borrado e sujo de propósito;
- a aprovação humana das versões antigas, que a carga de demonstração faz para montar o histórico;
- a caixa de e-mail: o código fala IMAP de verdade, testado contra um servidor local, mas as mensagens são simuladas;
- a entrada dos PDFs do acervo, feita pela carga de demonstração para rodar sem internet.

Leitura por LLM gravada: as leituras do acervo ficam salvas, então a demonstração mostra a dupla leitura sem chave de API. Um PDF novo precisa de chave para a segunda leitura.

Onde está cada coisa:

- o protótipo completo no ar, com o back-end: endereço e montagem na seção "Publicação" do `README.md`;
- a versão estática, no navegador: [gustavohenriquers.github.io/radar-cotador](https://gustavohenriquers.github.io/radar-cotador/), com a cotação calculada no próprio navegador;
- o [resumo em vídeo](https://gustavohenriquers.github.io/radar-cotador/video/radar-cotador-motion.mp4), de 41 s, a [demonstração completa](https://gustavohenriquers.github.io/radar-cotador/video/radar-cotador-demo.mp4), de 1 min 36 s, e os [slides](https://gustavohenriquers.github.io/radar-cotador/pdf/slides.pdf);
- como rodar: `README.md`;
- o roteiro da demonstração: `docs/roteiro-demo.md`;
- as medições e as regras em detalhe: `docs/detalhes-tecnicos.md`;
- como evoluir o sistema: `docs/como-evoluir.md`;
- as operadoras, uma a uma: `docs/operadoras/`;
- a pesquisa de fontes e normas: `docs/pesquisa/fontes-e-achados.md`;
- todos esses documentos em PDF: `docs/pdf/`.
