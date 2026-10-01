# Bradesco Saúde (ANS 005711)

Levantamento de 01/10/2026. Slug: `bradesco_saude`.

> **Depois deste levantamento**, o que ele apontou no leitor e no coletor foi corrigido no código, cada caso com teste (`docs/proposta.md`, seção 7):
> - material sem grade de preço por faixa (manual de coparticipação, portfólio) passou a gerar o aviso "nenhuma tabela de preço encontrada", em vez de sair com 0 preços em silêncio.

## Resumo

A Bradesco Saúde não publica tabela de preço. O site oficial (robots.txt `Allow: /`) mantém a área "Com Você Corretor", aberta sem login, com folders e portfólios das linhas, o manual de coparticipação com os limites em reais e a tabela de procedimentos. Os links dessas páginas ficam num array JavaScript, que a captura por página não lê; por isso a captura ativa é por endereço fixo. Preço só aparece no Portal de Negócios (login) e no material que o comercial manda ao corretor; nenhuma tabela pública apareceu em administradora. Rota recomendada: caixa de e-mail para preço, `url_direta` para coparticipação e portfólios, parceria com a operadora para escala.

## Canais verificados

| Canal | Endereço | O que tem | robots.txt / termos | Situação |
|---|---|---|---|---|
| Com Você Corretor (site oficial) | https://www.bradescoseguros.com.br/clientes/produtos/plano-saude/listas-de-hospitais-por-linha-de-planos | Página de apoio à venda "sem necessidade de login": rede por linha e estado, folhetos, reembolso, benefícios, coparticipação | `User-agent: *` / `Allow: /`. O sitemap não traz termos de uso do site, só os do WhatsApp e a política de dados | Público, sem preço |
| Portfólios de planos | https://www.bradescoseguros.com.br/clientes/produtos/plano-saude/portfolios-de-planos | 34 PDFs: folders do Efetivo por estado (18), Efetivo Plus (5), Regional (3), Premium (2), Nacional, Ideal, Nacional Plus, planos hospitalares; Portfólio SPG de 12/05/2026 e Empresarial de 11/05/2026 | Idem | Público. Links em `objArquivosDownload`, dentro de `<script>` |
| Coparticipação | https://www.bradescoseguros.com.br/clientes/produtos/plano-saude/coparticipacao-bradesco-saude | Manual de Coparticipação (15/07/2026, 217 KB) e tabela de procedimentos (24/08/2026, 1,22 MB) | Idem | Público. Links em `<script>` |
| Reajuste de contratos com menos de 30 pessoas | https://www.bradescoseguros.com.br/clientes/produtos/plano-saude/servicos/reajuste-contratos-coletivos-menos-de-30-pessoas | 14 listas do agrupamento, de 05/2013 a 04/2027, até 7,34 MB cada | Idem | Público, não baixado: é lista de contratos, e o percentual do agrupamento sai no dado aberto 055 da ANS |
| bradescosaude.com.br | https://www.bradescosaude.com.br/ | Redireciona para o site acima; o `/robots.txt` também redireciona para uma página HTML, sem regras | — | Sem conteúdo próprio |
| Portal de Negócios | https://wwwn.bradescoseguros.com.br/pnegocios2/wps/portal/portaldenegocios/ | Cotação e material do corretor | Login | Restrito, não acessado |
| Qualicorp (tabelasdevendas) | https://tabelasdevendas.qualicorp.com.br/tabelas/ | Manuais QualiPRO de várias operadoras; o buscador não trouxe nenhum do Bradesco | `/robots.txt` responde HTTP 403; o `Http` do projeto trata como proibido | Bloqueado |
| Aliança Administradora | https://aliancaadm.com.br/planos-de-saude/ | Lista a Bradesco Saúde (005711) entre as operadoras; preço só pelo simulador | `Disallow: /wp-admin/` | Sem PDF público |
| Arquivo da web | CDX de `www.bradescoseguros.com.br/wcm/connect/` | 2 cópias (2024) do manual de coparticipação de 15/02/2023 | Permite | Histórico ralo, sem captura |
| Corretoras e comparadores | Vários ("tabela Bradesco 2026") | Preços compilados de várias operadoras | — | Descartados (regra 4) |
| Entidades com contrato próprio | apesp.org.br (2020), sinasefese.org.br (QualiPRO Sergipe 2022) | Tabela do contrato de uma entidade, antiga | — | Vistos no buscador, não acessados |

## Captura configurada

Arquivo `fontes/operadoras/bradesco_saude.json`, fonte "Bradesco Saúde" (`site_operadora`, confiabilidade 5).

| Captura | Tipo | Ativa | Teste ao vivo | Por quê |
|---|---|---|---|---|
| Manual de coparticipação e tabela de procedimentos | `url_direta` | sim | 2 candidatos | Condição comercial vigente (limites para contratos a partir de 23/06/2026) |
| Portfólios SPG e Empresarial | `url_direta` | sim | 2 candidatos | Linhas, abrangência e rede de 3 a 199 pessoas e acima de 200 |
| Página de portfólios e folders | `pagina_publica` | não | 0 candidatos | Links dentro de `<script>`; o coletor só lê atributos de `<a>`, `<button>`, `<area>`, `<link>` e `<option>` |
| Página de coparticipação | `pagina_publica` | não | 0 candidatos | Mesmo motivo |
| Tabelas enviadas ao corretor | `caixa_email` | não | não testada (modelo) | Canal de preço. Remetentes `@bradescoseguros.com.br` e `@bradescosaude.com.br` |

- Os endereços usam a forma curta `wcm/connect/<uuid>/<arquivo>?MOD=AJPERES`, sem o `CACHEID`, que muda; a forma curta responde 200 com o mesmo PDF.
- Cada versão nova ganha outro uuid e a anterior sai do ar: o manual de 11/12/2024 (uuid `7bbf7823…`) responde 404. Na troca, a `url_direta` registra erro em vez de servir versão velha, mas o endereço novo tem de ser posto à mão. Como a data do nome vem em ddmmaa (`150726`), a chave de série também não liga uma versão à outra.
- Os dois domínios de e-mail têm MX e DMARC `p=reject` no DNS, o que atende a exigência de autenticação da captura. O buscador mostra contatos públicos para corretor em `@bradescoseguros.com.br` (ex.: digital@bradescoseguros.com.br, na página "Seja um corretor"); o HTML estático da página não traz o e-mail.

## Amostras e leitura

Pasta `amostras/operadoras/bradesco_saude/`, com `manifest.json`. Leitura geométrica, sem LLM.

| Arquivo | O que é | Páginas | Preços lidos | Colunas com registro ANS | Para revisar | Erros / alertas |
|---|---|---|---|---|---|---|
| `bradesco_manual_coparticipacao_2026-07-15.pdf` | Manual de coparticipação, 30% no SPG, limites em reais | 10 | 0 | 0 | 0 | 0 / 0 |
| `bradesco_portfolio_spg_2026-05-12.pdf` | Portfólio para empresas de 3 a 199 pessoas | 20 | 0 | 0 | 0 | 0 / 0 |
| `bradesco_folder_efetivo_plus_nacional_2026-09-21.pdf` | Folder do Efetivo Plus (SP, DF, RS, PR, BA, RJ), o arquivo mais novo da página | 11 | 0 | 0 | 0 | 0 / 0 |

Problemas do leitor:

- Zero é o resultado certo: nenhum dos três tem grade de preço por faixa etária, e nenhum cita registro ANS. O leitor, porém, devolve "0 preços em 0 colunas" sem achado de documento. Para o radar, um PDF sem grade de preço deveria ficar marcado como material de condição, e não como leitura vazia.
- A condição comercial está na página 4 do manual: limite em reais por evento (consulta eletiva, procedimentos seriados, pronto-socorro, procedimentos ambulatoriais, exames tipo A e tipo B, internação) para 8 colunas de linha (Regional GO e NOSP; Rio+ e São Paulo+; Efetivo; Efetivo Plus; Flex; Ideal; Nacional; Nacional Plus), de R$ 35,00 a R$ 600,00. O leitor não tem extração para essa grade.

## Na ANS

Índice local (`dados/ans/indice.sqlite`, PDA atualizado em 30/09/2026). Bradesco Saúde S.A., CNPJ 92.693.118/0001-60, seguradora especializada em saúde, ativa.

| Situação | Coletivo empresarial | Coletivo por adesão | Individual ou familiar | Total |
|---|---|---|---|---|
| Ativo | 321 | 56 | 0 | 377 |
| Suspenso | 200 | 94 | 58 | 352 |
| Cancelado | 1.614 | 309 | 100 | 2.023 |
| Transferido | 62 | 6 | 0 | 68 |
| Total | 2.197 | 465 | 158 | 2.820 |

- Ativos: 324 de abrangência nacional e 53 por grupo de municípios; 191 com coparticipação e 186 sem; 225 em quarto e 151 em enfermaria.
- 344 dos 377 ativos têm nota técnica de preço no índice; a mais recente é de 23/09/2026.
- Em 2026: 23 planos registrados, todos empresariais (ex.: Regional Pará e Premium SPP em setembro), e 1 suspensão.
- Outros registros do grupo: 421715 Bradesco Saúde – Operadora de Planos S/A (CNPJ 15.011.651/0001-54, o mesmo do rodapé do site; medicina de grupo), com 219 ativos, todos empresariais, 12 deles registrados em 2026; e 333689 Mediservice (o site da Bradesco tem páginas dela), com 795 ativos. Uma tabela da Bradesco pode trazer produto de qualquer um desses números; o radar precisa acompanhar ao menos 005711 e 421715.

## Lacunas e próximo passo

- Preço: não há canal público. Próximo passo: montar a caixa de e-mail que recebe o material do comercial ou da assessoria e, para escala, propor parceria com a Bradesco (o Portal de Negócios tem a cotação).
- Coletor: ler links que ficam em `<script>`, por exemplo com uma expressão configurável em `coletor/pagina.py` (aqui, `'arquivoUrl':'([^']+)'`). Com isso as duas capturas por página passam a descobrir os 34 folders e portfólios, o manual e a lista de procedimentos, e as `url_direta` podem sair.
- Leitor: extração da grade de limites de coparticipação (evento × linha) e um achado de documento quando não há grade de preço.
- Não verificado: o conteúdo do Portal de Negócios; se a Qualicorp ou a Aliança têm tabela da Bradesco em endereço público (o buscador não trouxe arquivo, e o tabelasdevendas está bloqueado); o e-mail exato pelo qual o comercial envia tabelas; a rede por linha (a página de rede não traz arquivos no HTML).
