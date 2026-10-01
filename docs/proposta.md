# Proposta: dados do Cotador obtidos, conferidos e atualizados sem digitação

**Gustavo Henrique** · desafio técnico do Cotador de Planos de Saúde · outubro de 2026

## Resumo

Hoje cada tabela que chega é lida e digitada à mão, plano por plano. Isso atrasa, abre espaço para erro e não acompanha a velocidade com que as tabelas mudam. A proposta é trocar a digitação por um **radar de dados**:
- o sistema busca o material onde ele é publicado;
- lê cada tabela duas vezes, de jeitos independentes;
- confere tudo contra os dados oficiais da ANS;
- chama uma pessoa só para o que não fecha.

Cada preço publicado guarda de onde veio, e o sistema avisa quando algo muda, antes de o corretor errar.

O protótipo que acompanha a proposta roda com material público real, e os resultados mostram que a ideia funciona:

- **81,1% dos preços passam sem revisão humana**, contando os produtos que o PDF identifica pelo registro ANS. O que sobra não é erro de leitura: são sinais da ANS sobre o preço ou sobre o plano, concentrados em poucas tabelas.
- **Em dois testes às cegas**, com 137 tabelas que o leitor nunca tinha visto, todo preço da primeira leitura foi confirmado pela segunda, sem nenhuma divergência.
- **As 9 operadoras do Cotador foram mapeadas uma a uma.** Nenhuma publica a tabela vigente aberta. O caminho é pelas administradoras, pelo e-mail e pela parceria, e o protótipo já tem cada um desses canais.
- **O sistema e o mapeamento acharam problemas reais que estavam passando:**
  - uma operadora extinta desde 2022 ainda listada na página do Cotador;
  - planos suspensos na ANS em tabela de venda;
  - uma tabela 9,7% mais barata porque era a versão antiga;
  - um hospital que saiu da rede de 9 planos publicados.
- **O custo é baixo:** a segunda leitura sai por cerca de US$ 0,001 por página. O acervo inteiro custou US$ 0,35.

O protótipo sobe com `docker compose up`, e o roteiro da demonstração está em `docs/roteiro-demo.md`.

| Pedido do desafio | Onde está |
|---|---|
| Obtenção dos dados, acessos, fontes indisponíveis ou restritas | seção 2 e `docs/operadoras/` |
| Redução do trabalho manual: o que é automático e quando entra uma pessoa | seção 3 |
| Confiabilidade e atualização: conferência, divergências, origem, vigência, histórico | seção 4 |
| Estrutura técnica: componentes, fluxo, armazenamento, crescimento | seção 5 |
| Plano de implementação: primeira entrega, etapas, riscos, dependências, medição | seção 6 |
| Os desafios que apareceram no caminho e como foram resolvidos | seção 7 |
| Protótipo: o que é real e o que é simulado | seção 8 e `README.md` |

As medições completas ficam em `docs/detalhes-tecnicos.md`, e o caminho para evoluir o sistema em `docs/como-evoluir.md`.

---

## 1. O problema

O desafio descreve dois problemas que se alimentam: o acesso às informações é limitado e a atualização é manual. Na ponta, o corretor recebe uma cotação que pode estar desatualizada e não tem como saber de onde veio o número.

Três coisas que a pesquisa mostrou e que guiaram a proposta:

- **O dado muda o tempo todo.** Só em 2026, um concorrente publicou pelo menos 225 avisos de mudança de tabela, em 106 dias diferentes. Com digitação, o dado sempre chega atrasado.
- **Ninguém tem API de preço.** Os concorrentes mantêm as tabelas com "mesa técnica" ou leem PDF com IA, e as APIs que as operadoras têm são de pós-venda, só para parceiros. Então o diferencial não está em "usar IA". Está em conferir, rastrear e avisar.
- **A desatualização já aparece hoje.** A página do Cotador lista a Saúde Sim, que teve o registro cancelado pela ANS em 2022 e a falência decretada em 2023. Uma checagem automática contra a ANS pegaria isso no primeiro dia.

No fim, o corretor precisa de três coisas: o preço certo, o preço atual e a segurança de saber de onde ele veio. A proposta é organizada em torno disso.

**Premissas:**
- **O que é o dado:** o preço por faixa etária de cada produto, identificado pelo registro ANS, em cada condição de venda (vidas, coparticipação, região, composição familiar). Ao lado dele: rede, reembolso, coparticipação e carências.
- **Material recebido:** o que a equipe já recebe por e-mail, WhatsApp ou portal pode ir para uma caixa dedicada ou ser subido numa tela.
- **Dados da ANS:** a ANS segue publicando os dados abertos que o sistema usa. A carga confere o formato, porque ele muda de vez em quando.
- **LLM:** usar um modelo de linguagem como segunda leitura é aceitável, com custo medido e sem publicar nada sozinho.
- **Portal com login:** só entra com autorização da operadora ou do corretor dono da conta.

**Escopo.** O protótipo se concentra no que trava o processo hoje: obter, ler, conferir e manter o preço atualizado. Ficaram de fora, de propósito:
- entrar em portal com login sem autorização;
- a rede de clínicas e laboratórios, que a ANS não publica e que pede um coletor por operadora;
- o motor de cotação em si. A cotação do protótipo existe para mostrar o dado chegando na ponta, e o Cotador já tem a sua.

---

## 2. Como conseguir os dados

**Começar pela ANS.** A ANS publica de graça, todos os dias, uma base que nenhum material de venda tem:
- o catálogo de planos, com contratação, acomodação, coparticipação, reembolso e situação de cada um;
- o preço de referência de cada plano por faixa etária, com a faixa de variação permitida;
- a rede hospitalar de cada plano;
- os pedidos de mudança de rede, com a data em que valem.

Não é a tabela de venda, mas é o que confere a tabela de venda. E é o que avisa que algo mudou mesmo quando não há acesso ao material.

**Ir aonde o material está.** As 9 operadoras da página do Cotador foram mapeadas uma a uma, por agentes de IA trabalhando em paralelo, com revisão humana de cada achado. Cada operadora tem um relatório em `docs/operadoras/`. A conclusão principal: **nenhuma publica a tabela vigente aberta no próprio site.** O preço chega de três jeitos, e o protótipo trata os três:

| Como o preço chega | Operadoras | O que o sistema faz |
|---|---|---|
| Administradoras que publicam as tabelas | NotreDame e Hapvida, pela Allcare, CORPe, Affix e Safe | coleta sozinho todo dia e baixa só o que mudou |
| Canal fechado (portal com login, material enviado ao corretor) ou fonte que não aceita robô | Bradesco, SulAmérica, Amil, CNU, Smile e Quallity | lê uma caixa de e-mail dedicada, só de remetente autenticado, e aceita upload na tela |
| Nenhum: operadora extinta | Saúde Sim | o radar avisa que o registro foi cancelado na ANS |

As operadoras de canal fechado são o lugar da **parceria**, que é o que escala de verdade. Enquanto ela não vem, o e-mail e o upload cobrem.

**Respeitar a fonte.**
- Sem login e sem contornar captcha.
- robots.txt obedecido, e lido do jeito certo (seção 7).
- Robô identificado e volume baixo.
- Onde os termos de uso proíbem robôs, como na Amil, o caminho é a parceria.
- Da rede, só prestador pessoa jurídica (LGPD). E nunca coletar de outro cotador.

**Quando a fonte está fechada, a ANS ainda avisa.** O protótipo já gera estes avisos:
- uma nota técnica registrada depois da tabela publicada quer dizer que tem tabela nova a caminho;
- um hospital com saída deferida avisa o corretor antes de a mudança valer;
- um plano suspenso vira alerta, e os preços dele vão para revisão.

---

## 3. Como tirar a digitação

O fluxo é o mesmo, de onde quer que o material venha:

```
recebe o PDF → lê duas vezes → confere → uma pessoa olha só o que não fechou → publica uma versão nova → avisa o que mudou
```

**Duas leituras independentes.**
- **A primeira é geométrica.** Acha os rótulos das faixas etárias e pega os valores pela posição na página. PDF escaneado passa antes por OCR.
- **A segunda é de um modelo de linguagem,** que lê cada página e entende a estrutura da tabela: produtos, condições, coparticipação, carências e vigência.

É a dupla digitação que já se usa para conferir cadastro manual, só que automática. Os dois leitores erram de jeitos diferentes: quando concordam, a confiança é alta; quando discordam, aquela célula vai para uma pessoa. O modelo de linguagem nunca publica nada sozinho.

**Uma terceira conferência, por cálculo.** A ANS exige que o contrato fixe o percentual de aumento entre as faixas etárias, e as operadoras usam os mesmos percentuais em toda uma linha de produtos. Então dá para recalcular cada preço a partir das outras colunas da própria tabela, ao centavo. Isso desempata quando as leituras discordam e pega dígito trocado: num teste com 1.434 erros de digitação plantados de propósito, o cálculo apontou todos os erros acima de 0,1% e 93% dos de centavos.

**O produto é identificado pelo registro na ANS, nunca pelo nome.** Há 344 nomes de plano repetidos dentro de uma mesma operadora. Com o registro, o catálogo da ANS completa o resto. Quando o PDF não traz o registro, como os da NotreDame, a proposta é uma pessoa ligar cada coluna ao produto uma vez por layout. O protótipo conta esses preços à parte, como "sem produto identificado".

| Automático | Com uma pessoa |
|---|---|
| Ler os preços, identificar o produto, preencher os atributos | Conferir as células apontadas, com o PDF ao lado e o número destacado |
| Conferir contra a ANS, contra a outra leitura e pelo cálculo | Aprovar, corrigir ou ignorar uma coluna |
| Comparar com a versão anterior e com outras fontes | Decidir a publicação, com um clique |
| Avisar o que mudou | Negociar acessos e parcerias |

**No acervo de teste:**
- **10.573 preços**, de 25 PDFs reais de 8 fontes, cada uma com um layout diferente, e de 1 PDF escaneado simulado;
- **80,1%** dos preços de produtos identificados passam sem revisão com uma leitura, e **81,1%** com as duas leituras e o cálculo;
- **o que vai para revisão não é erro de leitura.** Dos 899 preços apontados com uma leitura, 714 estão em duas tabelas que a regra da ANS questiona inteiras, 70 são de registros que não existem ou de planos cancelados, e 40 são de planos suspensos. Na prática, a pessoa decide uma dezena de casos, um por tabela, e não 899 células;
- **no PDF escaneado,** o OCR leu 352 de 360 preços sem errar nenhum. Os 8 que faltaram foram lidos pela segunda leitura e confirmados pelo cálculo.

---

## 4. Como garantir que o dado está certo e atual

**Regras com base legal.** Cada preço passa por regras que vêm da regulação, e não de achismo:

| Regra | O que verifica |
|---|---|
| Faixas etárias (RN 563) | a última faixa não passa de 6 vezes a primeira, e nenhum preço cai com a idade |
| Preço de referência (RN 564) | o preço contra a nota técnica do plano. Na Unimed Guarulhos, achou um preço de R$ 116,56 abaixo do piso de R$ 122,77 |
| Situação na ANS (RN 543) | plano suspenso, plano cancelado ou operadora cancelada sendo vendidos |
| Catálogo da ANS | registro que não existe: a Safe imprime um que não está no catálogo |
| Carências (Lei 9.656) | carência acima do máximo legal |
| Atributos | coparticipação e acomodação do material contra o registro na ANS |

Cada regra foi testada contra o acervo real antes de entrar, porque regra que acusa preço certo só atrapalha. Daí vieram quatro cuidados:
- tolerância de centavos, porque as operadoras usam o limite exato;
- reajuste igual em todas as faixas não é erro;
- preço com odonto embutido não segue a proporção das faixas;
- o preço tem de ser comparado com a nota técnica da época certa (seção 7).

**Origem, vigência e histórico.**
- **Origem:** todo preço publicado sabe de onde veio: documento, página, posição na página, forma de leitura e quem aprovou.
- **Versões:** nada é sobrescrito. Cada publicação é uma versão nova, e a anterior vira histórico.
- **Comparação pelo produto e pela condição de venda, não pela posição no PDF.** Na tabela de Rio Preto, as 14 colunas trocaram de lugar entre abril e maio, com os mesmos preços. Uma comparação por posição acusaria 14 reajustes; o sistema diz, corretamente, que nada mudou.
- **Material antigo nunca volta a ser o preço vigente.** Foi isso que deixou o arquivo da web montar sozinho o histórico da Allcare: entraram 9 versões antigas, sem mudar nenhuma cotação, e o sistema mediu, por exemplo, o reajuste de 24,4% da Unimed Fortaleza de agosto de 2024 para a versão seguinte.

**Divergências e dado desatualizado.**
- **Mesmo produto, preços diferentes em fontes diferentes:** o sistema avisa e diz qual material é mais novo. A mesma tabela Hapvida DF aparece na Allcare, na CORPe e na Affix. A da Affix está 9,7% abaixo porque é de 2025, e o corretor vê o alerta na cotação.
- **Toda cotação mostra a data do material de origem** e quando ele foi confirmado pela última vez.
- **A ANS avisa o resto:**
  - nota técnica nova depois da tabela: a SulAmérica registrou notas novas depois da tabela publicada em junho;
  - plano suspenso;
  - hospital saindo da rede: o Hospital Mogiano saiu de 9 planos publicados, e o Natal Hospital Center sai da rede da Unimed Natal em 26/10.
- **Na cotação, ao lado do preço,** aparecem a rede hospitalar do plano no estado do cliente e o que o registro diz sobre reembolso e coparticipação.

**O mesmo material dá sempre o mesmo resultado.** Leitura, cálculo, regras e histórico são determinísticos, e um teste lê o mesmo PDF duas vezes e compara o resultado. O modelo de linguagem é a única parte que não é. Por isso ele nunca decide sozinho, e cada leitura dele fica gravada: dá para refazer a conferência meses depois e chegar ao mesmo número.

---

## 5. Estrutura técnica e por que essas escolhas

```
 ANS (dados abertos) ─────────► índice ANS e rede hospitalar ───────────────────────┐
                                                                                    │
 páginas, APIs e arquivo da web ─┐                                                  ▼
 caixa de e-mail ────────────────┼─► coleta ─► PDF guardado ─► duas leituras ─► conferência ─► revisão ─► versão publicada ─► cotação e radar
 upload / parceria ──────────────┘
```

| Parte | Escolha | Por quê |
|---|---|---|
| Aplicação | Django + Django REST Framework | a stack do desafio; admin, migrações e ORM prontos, sem mágica para a equipe manter |
| Interface | React | a tela de revisão, com o PDF ao lado e a célula destacada, pede interação rica |
| Banco | PostgreSQL | versões, avisos e dados semiestruturados na mesma base, com transação na publicação |
| PDFs originais | disco no protótipo; armazenamento de objetos em produção | o PDF é a prova da origem e nunca se apaga |
| Primeira leitura | pdfplumber e OCR local | exata, grátis, explicável, e o documento não sai da empresa |
| Segunda leitura | modelo de linguagem barato (GPT-6 Luna), trocável por configuração | confirmou 10.570 de 10.573 preços por US$ 0,35; o Gemini teve a mesma qualidade por quase cinco vezes o custo |
| Dados da ANS | índice local montado dos dados abertos | consulta em milissegundos; da rede, baixa só o trecho de cada estado de um arquivo de 1,4 GB |
| Coleta | um motor só e tipos de captura pequenos; as fontes ficam em arquivos de configuração | fonte nova não pede código |
| Processamento | thread no protótipo; fila em produção | o documento é a unidade de trabalho, e os leitores não guardam estado |

**Para crescer em planos e operadoras:**
- **Operadora nova em PDF não pede código.** O leitor é genérico e já entende os layouts das 8 fontes do acervo, mais os que o mapeamento trouxe.
- **Fonte nova é um arquivo de configuração.**
- **Tipo de captura novo é uma classe pequena.** O da API pública da CORPe saiu com 40 linhas e trouxe 53 tabelas.
- **Custo:** mil PDFs de 15 páginas por mês custariam uns US$ 15 de leitura, e documento repetido não é relido.

---

## 6. Plano de implementação

| Fase | Entrega | Valor |
|---|---|---|
| **1 (semanas 1 e 2)** | **Saúde da base atual:** cruzar o que o Cotador já tem cadastrado com a ANS (operadoras canceladas, planos suspensos, registros que não existem) e mostrar a rede e o reembolso do registro oficial ao lado de cada plano | valor no primeiro dia, sem mudar o processo da equipe |
| **2 (semanas 2 a 6)** | Dupla leitura, tela de revisão e publicação versionada, começando pelas administradoras que já estão configuradas e pela caixa de e-mail | a digitação vira revisão do que foi apontado |
| **3 (semanas 6 a 10)** | Radar de mudanças (preço, rede, divergência, vigência, nota técnica nova), selo de origem na cotação e coleta agendada | o dado passa a avisar antes de o corretor errar |
| **4 (depois)** | Parcerias com as operadoras de canal fechado e com plataformas como a Planium; envio de tabelas pelos corretores; rede de clínicas e laboratórios | cobertura e atualização perto do tempo real |

**A primeira entrega é de propósito a mais simples.** Ela não depende de nenhuma operadora e já mostra o valor: só a checagem contra a ANS pegaria a Saúde Sim.

**Riscos e como são tratados:**
- **A operadora não publica o preço.** É o caso de 6 das 9. O sistema reduz o trabalho e o erro, mas não substitui a relação com a operadora: por isso e-mail agora e parceria depois.
- **Um layout que o leitor não entende.** A segunda leitura cobre, a divergência vai para uma pessoa, e a correção entra no leitor genérico, nunca como caso especial (seção 7).
- **O modelo de linguagem erra ou fica caro.** Ele nunca publica sozinho, o custo é medido por página, e o provedor troca por configuração.
- **A fonte muda de formato.** O coletor avisa quando uma página que listava tabelas passa a não listar nenhuma.
- **A fonte troca o nome do arquivo entre versões.** O histórico se parte em dois. O próximo passo é reconhecer a tabela pelo conjunto de registros ANS que ela traz.
- **LGPD.** Só dado de pessoa jurídica, e nenhum dado de beneficiário.

**Dependências:**
- acesso da equipe ao material que ela já recebe;
- uma chave de provedor de LLM (OpenAI, Google ou Anthropic);
- o contato comercial para as parcerias;
- a decisão de qual base do Cotador cruzar na fase 1.

**Como saber se funcionou:**
- **Tempo até o Cotador:** do material publicado pela operadora até a tabela disponível para o corretor.
- **Automação:** a parte dos preços publicados sem revisão. A meta inicial é 75%, e o protótipo chega a 81,1%.
- **Qualidade:** erros achados depois de publicar, em reclamações e correções.
- **Frescor:** a idade média do material por trás das cotações.
- **Cobertura:** operadoras e planos com tabela vigente.
- **Custo** por tabela processada.

---

## 7. Desafios que apareceram e como foram resolvidos

Rodar com material real trouxe problemas que nenhum desenho no papel mostraria. O mapeamento das operadoras, feito com agentes de IA, trouxe PDFs e sites diferentes de tudo o que o acervo tinha, e cada falha exposta virou correção com teste. Nenhuma correção mudou o que já funcionava: o acervo segue lendo os mesmos 10.573 preços.

1. **O modelo de linguagem resumia os documentos longos.** Lendo o PDF inteiro de uma vez, ele pulava tabelas e confirmava só 28% dos preços. Com cada página enviada separadamente, em paralelo, a confirmação foi a quase 100%. O custo subiu pouco mais da metade e continuou perto de US$ 0,001 por página.

2. **Uma coluna de preços que ninguém via.** Um PDF da NotreDame carregava uma coluna escondida na borda da grade. A leitura geométrica lia; os dois modelos testados, que veem a página, não. Agora o leitor confere cada palavra contra a página desenhada e descarta o que ninguém vê.

3. **Reajustes que não existiam.** Comparando versões pela posição das colunas, a tabela da Qualicorp de 2024 contra a de 2026 casava "titular + 1 dependente" com "titular + 2 ou mais", e mostrava "reajustes" de −21% a +15% no mesmo produto. A comparação passou a usar a condição de venda: vidas, coparticipação e composição familiar. Reordenar colunas agora gera zero reajustes, e a Qualicorp mostra o que de fato mudou: 26 tabelas com preço novo, 13 condições encerradas e 4 produtos que saíram.

4. **Coluna incompleta passando como resolvida.** O alerta de faixa faltando não mandava nada para revisão, porque a faixa que falta não tem célula. Agora a coluna inteira vai para revisão.

5. **O robots.txt lido errado pela própria biblioteca do Python.** O leitor padrão liberava o site inteiro da Unimed Guarulhos, por causa de uma linha em branco, e ignorava os curingas da NotreDame. Um coletor que confiasse nele baixaria justamente o que essas fontes pedem para não baixar. O coletor passou a ler o robots.txt seguindo a norma (RFC 9309), com teste para cada caso.

6. **Uma versão antiga podia virar o preço do dia.** Uma cópia de 2024, vinda do arquivo da web ou reenviada por alguém, substituiria o preço de 2026. Agora o material antigo entra no histórico, na posição da sua data, e nunca volta a ser o preço vigente, em qualquer ordem que os documentos cheguem.

7. **Layouts que quebravam o leitor.** Todos foram resolvidos no leitor genérico, sem caso especial para nenhum arquivo:
   - **dígito desenhado à parte:** num PDF da NotreDame, o "1" de "118,07" era uma palavra separada, e 735 preços perdiam a centena. O pior: o cálculo confirmava parte deles, porque o erro se repetia igual em várias colunas;
   - **tabelas em camadas:** duas tabelas de anos diferentes sobrepostas, misturadas letra a letra;
   - **negrito falso:** a mesma letra desenhada duas vezes no mesmo lugar;
   - **condição na vertical:** "Com coparticipação" escrito girado ao lado da grade;
   - **rótulos de faixa novos:** "Acima 59 anos", "> 59", e o "59" com o "ou +" na linha de baixo.

   O teste do acervo inteiro é o que garante que uma correção não quebra outra. Ele pegou, por exemplo, o primeiro filtro de camadas apagando metade dos preços de uma tabela cujo fundo das células é desenhado por cima do texto. O filtro passou a agir só quando há camadas de texto empilhadas.

8. **Alarme falso por comparar com a nota técnica errada.** Uma tabela de 2023 comparada com a nota técnica de 2026 gerava 112 alertas falsos de preço abaixo do custo. A data da nota na ANS é a do registro, que pode vir antes ou depois de a tabela valer. Agora o preço é comparado com as notas plausíveis para a época do material, e o alerta só fica quando nenhuma delas explica o preço. O que era verdade virou um aviso próprio: existe nota técnica mais nova, então a tabela provavelmente está defasada.

9. **Cópias com defeito no arquivo da web.** Cinco versões antigas da Allcare estavam cortadas em 1 MiB no próprio arquivo. Agora o PDF é aberto antes de ser registrado, e a cópia com defeito fica marcada e não é pedida de novo.

10. **Endereços que o navegador aceita e o código não.** A API da CORPe devolve links com espaço, e 50 das 53 tabelas falhavam. O coletor passou a pedir o endereço do jeito que o navegador pede.

11. **Leituras em paralelo derrubando umas às outras.** Ler 84 documentos ao mesmo tempo mostrou que o índice da ANS dividia uma única conexão entre as leituras. Agora cada leitura tem a sua.

Hoje são 115 testes automatizados, e um comando (`./verificar.sh`) roda todos, junto com a validação das fontes e o build da interface.

---

## 8. O protótipo: o que é real e o que é simulado

**Real:**
- os dados abertos da ANS, baixados do portal oficial;
- os 25 PDFs do acervo, públicos, com origem, data e hash em `amostras/manifest.json`;
- as coletas:
  - a página de materiais da Allcare;
  - as versões antigas no arquivo da web;
  - as 53 tabelas da API da CORPe;
- o mapeamento das 9 operadoras, com as amostras lidas;
- a rede hospitalar e as mudanças de rede, da ANS;
- todo o pipeline: leitura, OCR, conferência, publicação versionada, comparação de versões, radar e cotação.

**Simulado:**
- o PDF escaneado, gerado a partir da tabela real da Unimed Guarulhos, torto, borrado e sujo de propósito;
- a aprovação humana das versões antigas, que a carga de demonstração faz para montar o histórico;
- a caixa de e-mail: o código fala IMAP de verdade e foi testado contra um servidor de e-mail local, mas as mensagens são simuladas;
- a entrada dos PDFs do acervo, que vêm pela carga e não pela coleta, para a demonstração rodar sem internet.

**Leitura por LLM:** as leituras do acervo estão gravadas, então a demonstração mostra a dupla leitura sem chave de API. Um PDF novo precisa de chave para a segunda leitura; sem ela, o sistema funciona com uma leitura só e todas as regras.

**Onde está cada coisa:**
- como rodar: `README.md`;
- o roteiro da demonstração: `docs/roteiro-demo.md`;
- as medições e as regras em detalhe: `docs/detalhes-tecnicos.md`;
- como evoluir o sistema: `docs/como-evoluir.md`;
- as operadoras, uma a uma: `docs/operadoras/`;
- a pesquisa de fontes e normas: `docs/pesquisa/fontes-e-achados.md`.
