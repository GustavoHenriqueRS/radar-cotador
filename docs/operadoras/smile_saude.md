# Smile Saúde (ANS 395480)

Levantamento de 01/10/2026. Slug: `smile_saude`.

> **Depois deste levantamento**, o que ele apontou no leitor e no coletor foi corrigido no código, cada caso com teste (`docs/proposta.md`, seção 7):
> - "&gt; 59 anos" passou a ser lido como a última faixa (70 de 70 preços na cópia de 01/2023);
> - "Com coparticipação" e "Sem coparticipação", escritos na vertical ao lado das grades, viraram a condição de cada grade.

## Resumo

A Smile não publica tabela de preço nem condição comercial própria no site; há só uma página que explica o reajuste individual da ANS. O material chega ao corretor por canal fechado: plantão de vendas por WhatsApp, administradoras e portal com login. A única tabela pública achada é a de adesão no DF que a Allcare publicou em 2023. O arquivo saiu da página de materiais, mas segue no ar, e os 7 produtos dele estão cancelados ou suspensos na ANS. Rota recomendada: caixa de e-mail que receba as tabelas da Smile (modelo deixado inativo). Se a Allcare voltar a listar a Smile, a captura que já existe da Allcare pega o arquivo sem configuração nova.

**Divergências a apontar no radar**

- **Nome e UF.** O registro 395480 é da ESMALE ASSISTENCIA INTERNACIONAL DE SAUDE LTDA. (CNPJ 37.135.365/0001-33), nome fantasia SMILE, com sede em Maceió/AL e ativa. O nome fantasia bate com "Smile Saúde"; a razão social, não.
- **DF fechado na ANS.** A pesquisa anterior trata a Smile como operadora do DF. Na ANS, nenhum dos 28 produtos com "DF" no nome está ativo: 18 estão cancelados (o último em 09/05/2024) e 10 suspensos (o último em 28/07/2023). O site ainda mostra o cartão "AMBULATORIAL DF – produto exclusivo na praça Brasília". Dos 6 produtos com "AMBULATORIAL" e "DF" no nome, 2 estão suspensos desde 20/04/2023 (Ambulatorial Top DF, adesão e empresarial) e 4 foram cancelados entre 27/02 e 09/05/2024.

## Canais verificados

| Canal | Endereço | O que tem | robots.txt / termos | Situação |
|---|---|---|---|---|
| Site da operadora | https://www.smilesaude.com.br/ | Cartões de plano (MOBI, Premium Promo, Platinum Promo, Ambulatorial DF), página de reajuste individual, áreas com login (cliente, empresa, administradora, prestador). Nenhuma tabela, nenhuma área de corretor. | robots.txt responde 404 (sem restrição). O rodapé diz que todo o conteúdo é de uso exclusivo da Smile. | Público, sem material de venda |
| Rede para quem não é cliente | /rede-credenciada-smile/acesso.html, /rede-credenciada.php | Rede dos "planos comercializados atualmente", por formulário e JavaScript. A busca na web acha PDFs de rede por linha (ex.: `rede-credenciada-smile/files/REDE_PLATINUM.pdf`), que não baixei. | Idem | Público. É rede, não preço: fora do leitor |
| Link "Quero comprar" | https://compresmile.online/ | Está comentado no HTML da home. O domínio está estacionado ("may be for sale"). | robots.txt típico de estacionamento | Morto |
| Allcare: página de materiais | https://www.corretorallcare.com.br/materiais-de-vendas | 96 tabelas em PDF. No DF, só Hapvida e MedSênior; nenhuma da Smile. | Permite (`Disallow: /cgi-bin/`, `Disallow: /wusage`) | Captura da Allcare já ativa no projeto |
| Allcare: arquivo fora da página | https://www.corretorallcare.com.br/arquivos/pdf/tabelas/tabela_unica_adesao_smile_df.pdf | Tabela de adesão Smile DF, 9 páginas, 7 produtos. Last-Modified de 02/06/2023. | Permite. O PDF diz "material de uso interno, destinado exclusivamente aos consultores". | No ar, sem link; produtos cancelados ou suspensos |
| Allcare no arquivo da web | API CDX do web.archive.org | Uma cópia do mesmo endereço, de 23/01/2023 | Permite (o robots.txt da Allcare vale para a cópia) | Histórico. A CDX respondeu 503 uma vez e funcionou na segunda tentativa |
| Aliança Administradora | https://aliancaadm.com.br/e/convenios/prefeituramunicipaldemaceio/ | Lista a Smile (395480) entre as operadoras parceiras, sem tabela pública. A URL irmã `/e/orgao-publico/...` respondeu HTTP 500. | Permite (`Disallow: /wp-admin/`) | Sem material público |
| Easyplan (administradora, DF) | https://easyplan.com.br/ | Site só em JavaScript: o HTML não cita a Smile. `www.easyplan.com.br` tem certificado inválido e o cliente HTTP o trata como bloqueado. | Permite (exceto `/analiseeasysite`, `/pesquisa/`) | Vínculo com a Smile não confirmado |
| Sites de corretoras com a marca no domínio | smilesaude.net.br, redesmile.net, smilesaudealagoas.com.br, smilejoaopessoa.com.br, smilecampinagrande.com.br | Captação de contato, preços em HTML, nenhum PDF oficial. Alguns dizem que a tabela é exclusiva do corretor. | Não se aplica | Não usados: não são canal oficial |
| Comparadores de várias operadoras | medlifeseguros.com.br, planodesaude.net.br, seu-convenio.com | Preços e dados transcritos | Não se aplica | Não usados (regra do projeto) |

Restrito, não acessado: as áreas de cliente, empresa, administradora e prestador do site, e os portais de corretor das administradoras.

## Captura configurada

Arquivo: `fontes/operadoras/smile_saude.json`.

- **Smile Saúde** (`site_operadora`): caixa de e-mail `caixa_email` inativa, como modelo, com remetente `@smilesaude.com.br`. É o domínio do e-mail cadastrado na ANS. Não há captura de página porque o site não publica material de venda.
- **Allcare** (mesmo nome e tipo da fonte existente; o carregador junta as capturas):
  - `url_direta` **inativa** para o arquivo fora da página. A descoberta funciona ao vivo (1 candidato) e o robots.txt permite. Fica inativa porque a Allcare tirou o link da página: o arquivo não é mais a tabela vigente que `url_direta` pressupõe. Serve de auditoria e de caso de teste.
  - `wayback` **inativa** para o mesmo endereço. A descoberta ao vivo achou 1 cópia (23/01/2023), com o robots.txt do original permitindo. É histórico, como a captura de arquivo da web que já existe na Allcare.
- `python -m coletor.fontes` valida sem problemas.

## Amostras e leitura

Pasta `amostras/operadoras/smile_saude/` (hash e origem em `manifest.json`). Saídas em `saidas/`.

| Arquivo | Páginas | Preços lidos | Colunas (com registro ANS) | Confirmados pelo cálculo | Para revisão | Erros | Alertas |
|---|---|---|---|---|---|---|---|
| `allcare_smile_adesao_df_2023-06.pdf` | 9 | 70 de 70 | 7 (7) | 14 | 70 | 5 | 2 |
| `wayback_allcare_smile_adesao_df_2023-01-23.pdf` | 6 | 63 de 70 | 7 (7) | 50 | 63 | 5 | 9 |

O que o leitor acertou:

- Em `allcare_smile_adesao_df_2023-06.pdf`, os 70 valores conferem com o texto do PDF e cada coluna ficou com o registro certo.
- Os 5 erros são planos cancelados: 482.588/19-8, 482.592/19-6 e 482.594/19-2 desde 27/02/2024; 482.593/19-4 e 482.596/19-9 desde 09/05/2024.
- Os 2 alertas são planos suspensos desde 28/07/2023: 482.591/19-8 e 482.595/19-1.
- Entre as duas versões, os 63 preços comparáveis subiram exatamente 29,8%, igual em todas as colunas e faixas. É o reajuste de abril de 2023 ("Reajuste: Abril" impresso).

Problemas do leitor:

1. **Faixa "> 59 anos" não reconhecida.** Arquivo `wayback_allcare_smile_adesao_df_2023-01-23.pdf`, página 2. O rótulo traz o sinal antes do número, e `_RE_FAIXA` em `leitor/faixas.py` só aceita "59" no começo ("59 anos >", "59+").
   - A linha 59+ das duas grades se perdeu: 7 preços, com o alerta "faixas não lidas: 59+" em todas as colunas.
   - A linha 59+ da grade de cima (R$ 1.520,30 / 1.539,00 / 1.720,33) entrou no rótulo das colunas da grade de baixo, por exemplo "1.520,30 R$ PREMIUM PROMO DF APARTAMENTO".
   - Precisa de correção no código central.
2. **Condição de coparticipação não capturada** nos dois arquivos (`condicao` vazia nas 14 colunas). Os rótulos "Com coparticipação" e "Sem coparticipação" ficam abaixo da grade na versão de 06/2023 e ao lado do título na de 01/2023. Aqui os registros distinguem as grades e a ANS informa o fator moderador. Num material com o mesmo registro nas duas grades, a condição se perderia.
3. **Rótulos de coluna com texto do título**, por exemplo "Obstetrícia Opus Enfermaria", "com Premium Promo Apartamento" e "VENDAS Coletivo por Adesão com...". É só cosmético.
4. **Nenhum aviso de documento.** O material não traz data de vigência impressa, e a idade (2023) só aparece pelo Last-Modified.

## Na ANS

Índice local `dados/ans/indice.sqlite` (pda-008 de 30/09/2026) e CADOP.

- Operadora ativa, medicina de grupo, Maceió/AL, registrada em 16/12/1998.
- 174 planos: 23 ativos, 108 suspensos e 43 cancelados.

| Contratação | Ativo | Suspenso | Cancelado |
|---|---|---|---|
| Coletivo por adesão | 9 | 38 | 27 |
| Coletivo empresarial | 9 | 33 | 15 |
| Individual ou familiar | 5 | 37 | 1 |

- **Ativos:**
  - Linhas: EASY NE, MOBI, Premium Promo CP, Platinum Life CP e três planos-referência antigos.
  - Segmentação: 20 são ambulatorial + hospitalar com obstetrícia, 20 têm coparticipação e nenhum é só ambulatorial.
  - Abrangência: 12 municipais, 9 de grupo de municípios e 2 de grupo de estados.
  - Os 23 têm nota técnica (VCM); a mais recente é de 07/05/2025.
- **Mudanças recentes**, pela data da situação atual de cada plano:
  - situação "Ativo" desde 14/05/2025 (4 planos) e desde 10/05/2025 (2);
  - em 2024, 26 suspensões (8 em 19/02 e 18 em 17/06) e 25 cancelamentos (10 em 27/02 e 15 em 09/05).
- **Qualidade do dado:** 25 nomes de plano da Smile vêm com tabulações no fim (ex.: "EASY NE - 3111E\t\t\t"), 6 deles ativos. Casar por nome falharia; por registro, não.

## Lacunas e próximo passo

- **Não há tabela vigente pública da Smile.** O próximo passo é a caixa de e-mail: um corretor parceiro encaminha o material da Smile, com remetente `@smilesaude.com.br` autenticado por DMARC ou DKIM. Ou uma parceria com a operadora ou com uma administradora parceira (Aliança, por exemplo).
- **Não verifiquei** quais municípios cada plano ativo cobre: o índice local não tem a tabela de municípios. Também não confirmei se a Smile ainda vende no DF por algum produto de abrangência "grupo de estados".
- **Easyplan:** o site só renderiza com JavaScript. Ficou sem verificação se ela administra planos da Smile.
- **Correção no leitor:** aceitar "> 59 anos" e variantes em `leitor/faixas.py`; ler o rótulo de coparticipação abaixo ou ao lado da grade.
