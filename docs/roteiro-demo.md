# Roteiro da demonstração (5 minutos)

1. **Painel (20 s).**
   - 6.892 preços lidos de PDFs reais no acervo inicial, 86% sem precisar de gente, e o que falta está apontado.
   - Em "Operadoras do Cotador", cada uma das 9 operadoras da página de vocês aparece com a situação na ANS e por onde o preço chega. A Saúde Sim aparece cancelada desde 2022, e está extinta.

2. **Documento `unimed_guarulhos_pme_2026.pdf` (60 s).**
   - O PDF real da Unimed Guarulhos, com cada preço destacado no lugar de onde saiu: 360 preços, 1 apontado.
   - Clicar na célula 0–18 do Essencial III: R$ 116,56, abaixo do piso da nota técnica que a própria operadora registrou na ANS (R$ 122,77).
   - Mostrar a grade e a regra. Aprovar ou corrigir: é aqui que a pessoa entra, e só aqui.

3. **O mesmo PDF escaneado (20 s).**
   - Versão "escaneada" (simulada, torta e suja). O OCR leu 352 de 360 preços, sem nenhum errado, e achou o mesmo problema.
   - A segunda leitura completa o OCR: o LLM leu os 8 preços que faltavam e errou 3 dígitos que o OCR acertou.
   - E o cálculo desempata: pelo percentual de faixa das outras colunas, os 3 dígitos certos são 474,77, 892,23 e 767,05, os do OCR. Das 12 células que iam para revisão, sobra 1, o preço abaixo do piso da ANS.

4. **Radar (40 s).**
   - Unimed BH: reajuste de +18,5% medido sozinho entre as versões de 2024 e 2026.
   - Rio Preto: as colunas trocaram de lugar e o sistema não se confundiu (comparação pelo registro ANS); 2 produtos saíram da tabela em agosto.
   - Affix × CORPe: o mesmo produto 10,7% mais barato na Affix, porque a tabela dela é de 2025.
   - Rio Preto, abril e maio: 2 planos com venda suspensa na ANS desde 11/2024 ainda na tabela. FERJ: a vigência venceu em 30/09/2026, e o radar pede a versão nova.
   - Qualicorp: a operadora juntou "titular" e "titular + 1" numa tabela só. O sistema compara cada composição com a mesma composição (reajuste mediano −10,8%) e avisa que a condição de venda mudou, em vez de inventar reajuste.
   - Rede: a ANS deferiu a saída do Hospital Mogiano da rede de 9 planos publicados. Nenhum PDF de venda conta isso; o registro oficial conta, com data e protocolo.

5. **Cotação (60 s).**
   - Idades 38, 36 e 9. O mais barato é a Affix, mas o cartão avisa: material de 08/2025, CORPe e Allcare têm o mesmo produto 10,7% mais caro com material de 2026.
   - É o erro que o corretor cometeria hoje sem saber.
   - Escolher a UF do cliente (RN). Cada cartão mostra:
     - o que o registro na ANS diz: reembolso, coparticipação, acomodação, abrangência;
     - quantos hospitais o plano tem no estado, quantos com pronto-socorro;
     - a lista, aberta num clique.
   - No Essencial Flex da Unimed Natal: "Natal Hospital Center sai em 26/10/2026, no lugar entram Casa de Saúde São Lucas e Hospital Unimed". Num plano municipal da Hapvida: "nenhum hospital da rede em RN". Tudo dos dados abertos da ANS.

6. **Fontes (60 s).**
   - Cada fonte tem suas capturas. Allcare → Página de materiais → Coletar agora: o coletor acha as 96 tabelas, reconhece pelo hash as que já estão no acervo e baixa e lê sozinho as novas.
   - Teste às cegas: das 84 tabelas novas, nunca vistas pelo leitor, os 8.553 preços da leitura geométrica foram todos confirmados pelo LLM, por US$ 0,56. Na segunda coleta, nada é baixado de novo (ETag).
   - Allcare → Histórico no arquivo da web: as versões que a Allcare já tirou do ar entram no histórico, sem mudar a cotação. Em Tabelas → Histórico, a Unimed Fortaleza mostra +24,4% desde agosto de 2024. O arquivo guardou 5 cópias truncadas, e o coletor as recusou.
   - Unimed Guarulhos: o site bloqueia robôs, e o sistema obedece. O canal que funciona é o e-mail: com o perfil `email` ligado e `simular_email` enviado, Coletar agora aceita só a mensagem autenticada da operadora, com a tabela dentro de um .zip, e ignora a falsificada.
   - CORPe → API de materiais: a página da CORPe é feita em JavaScript e não tem link no HTML. O mapeamento da Hapvida achou a API aberta por trás dela, e o tipo de captura novo, de 40 linhas, traz as 53 tabelas Hapvida com a data de cada versão. No teste às cegas, os 3.000 preços da leitura geométrica foram todos confirmados pelo LLM.
   - Fonte nova é um arquivo JSON em `fontes/`; tipo de captura novo é uma classe pequena no mesmo motor.

7. **Fecho (20 s).**
   - Operadora nova em PDF não pede código. Fontes restritas viram pedidos dirigidos, disparados pelos sinais da ANS.
   - A segunda leitura (GPT-6 Luna) confirmou 10.570 de 10.573 preços do acervo, célula a célula, por US$ 0,35 no total: é a dupla digitação, automática. O Gemini 3.8 Flash empatou em acerto, por quase 5 vezes o custo.
   - E ela já pegou um erro da leitura geométrica: um PDF da NotreDame esconde uma coluna de preços que ninguém vê na página; a geométrica lia, os dois LLMs não. Hoje o leitor descarta texto invisível.
