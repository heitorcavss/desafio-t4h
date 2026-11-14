# Experimentos

Uma linha por ideia aplicada. Todo número de antes e depois vem do `scripts/medir.sh` (pastas em `resultados/`), e cada valor é a **mediana das 3 execuções**. Parâmetros iguais em todas as medições: 20 usuários virtuais, 60 s, semente 42.

**Antes usado:** a linha de base (aplicação original), nas 3 pastas abaixo. Cada mudança da tabela é comparada com ela. A mudança 02 também é comparada com a mudança 01, as mudanças 03 e 04 com a 02, a mudança 05 com a 03 (código final do pool, `max` 10) e a mudança 06 com a 05 (em uma ronda intercalada, nas mesmas condições da máquina), para isolar o efeito de cada uma (veja as notas). A mudança 07 é comparada com a 06, mas em sessões diferentes da máquina (veja a nota da 07). A mudança 08 é comparada com a 07 em uma ronda intercalada. A mudança 09 é comparada com as 3 execuções da 08 (`08-intercalado`) e, como conferência, com 2 execuções da 08 medidas na mesma sessão, sem intercalar. A mudança 10 é comparada com 2 execuções da mudança 09 com os limites de CPU antigos, medidas no mesmo dia (`09-controle`, commit `2be7878`); as colunas "→" da tabela continuam contra a linha de base.

- Linha de base: [171102](resultados/20261104-171102-00-linha-de-base/resumo.txt), [171309](resultados/20261104-171309-00-linha-de-base/resumo.txt), [171510](resultados/20261104-171510-00-linha-de-base/resumo.txt) (commit medido: `8134893`)

## Resultados

| # | Mudança | Hipótese | Fonte | Status | req/s | p95 (ms) | CPU banco | Memória banco | CPU API | Pastas (depois) | Conclusão |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 | Índices em `pedidos.cliente_id`, `itens_pedido.pedido_id` e `lower(email)` (`banco/03-indexes.sql`, commit `2b6901a`) | Criar índices nas colunas que as rotas filtram (`pedidos.cliente_id`, `itens_pedido.pedido_id` e `lower(email)`) deve reduzir o tempo das consultas e a CPU do banco, porque o banco deixa de ler as tabelas inteiras (Seq Scan) e descartar quase todas as linhas. | [Índices (PostgreSQL 16)](https://www.postgresql.org/docs/16/indexes-intro.html), [índices sobre expressões](https://www.postgresql.org/docs/16/indexes-expressional.html), Silberschatz cap. 23 (p. 596) | Aplicada e medida | 1,68 → 3,93 | 41966,6 → 16433,0 | 96,4% → 98,5% | 399,9 → 398,8 MiB | 9,3% → 15,5% | [024453](resultados/20261109-024453-01-indices/resumo.txt), [024643](resultados/20261109-024643-01-indices/resumo.txt), [024823](resultados/20261109-024823-01-indices/resumo.txt) | Depois dos índices, a latência diminuiu bastante e as requisições por segundo aumentaram, por conta da velocidade das consultas. Um comportamento esperado, porém não pensado, foi o aumento da CPU: ele vem do aumento de requisições por segundo, e significa que as consultas ficaram mais baratas (cada uma gasta menos CPU). A CPU da própria API também subiu, porque, com mais requisições por segundo, ela é mais utilizada. (A do banco subiu pouco, de 96,4% para 98,5%, porque já estava perto do limite.) |
| 02 | Rota `/clientes/:id/pedidos` com um `JOIN` no lugar das consultas em loop (`api/src/rotas.js`, commit `8ce1978`) | Ao alterar a rota `/clientes/:id/pedidos` provavelmente diminuirá o tempo de latência da rota específica, pois diminuirá o número de consultas e, por consequência, o de conexões ao banco de dados. Dessa forma, podendo acarretar em uma diminuição no uso da CPU, visto que a rota ficará mais responsiva. | [Wellhausen (2008), "Object Prefetch Filter"](https://www.tim-wellhausen.de/papers/ObjectPrefetchFilter/ObjectPrefetchFilter.html); [Phabricator, N+1](https://secure.phabricator.com/book/phabcontrib/article/n_plus_one/); [OpenReplay, N+1](https://blog.openreplay.com/n-1-query-problem/); Silberschatz cap. 23 (p. 598-599) | Aplicada e medida | 1,68 → 6,27 | 41966,6 → 16796,6 | 96,4% → 100,1% | 399,9 → 403,5 MiB | 9,3% → 15,0% | [162701](resultados/20261109-162701-02-join/resumo.txt), [162849](resultados/20261109-162849-02-join/resumo.txt), [163030](resultados/20261109-163030-02-join/resumo.txt) | Depois do JOIN, a latência da rota `/clientes/:id/pedidos` diminuiu muito (a mediana foi de 7390,8 para 598,5 ms), porque ela deixou de fazer várias consultas e passou a fazer duas (no cliente 42, pela contagem do código; as conexões eu não medi diretamente). As requisições por segundo aumentaram (de 3,93 para 6,27), porque a rota ficou mais rápida. Só que a CPU não diminuiu como eu tinha pensado: o banco chegou ao limite (100,1%), porque, com mais requisições por segundo, ele continua trabalhando no máximo. O que diminuiu foi a CPU por requisição: o banco gasta menos CPU para atender cada uma (cerca de 25 por req/s na mudança 01 contra cerca de 16 na 02). Essa é uma conta que eu fiz, dividindo a CPU média pela vazão, e não um número do `medir.sh`. O p95 geral ficou igual (16433,0 → 16796,6 ms), porque os tempos mais lentos agora vêm de outras rotas, que eu não mexi. |
| 03 | Pool de conexões no lugar de uma conexão por consulta, com `max: 10` (`api/src/db.js`, commit `cebdf56`) | A implementação do pool pode acarretar a diminuição do tempo de latência geral da API, visto que o tempo para abrir uma conexão nova é consideravelmente maior do que o de reaproveitar uma conexão já aberta, implicando diretamente nas requisições por segundo e na diminuição do custo de CPU de uma requisição única, ou seja, mais req/s. | [node-postgres, Pooling](https://node-postgres.com/features/pooling); [Percona (Camargos, 2018)](https://www.percona.com/blog/2018/06/27/scaling-postgresql-with-pgbouncer-you-may-need-a-connection-pooler-sooner-than-you-expect/); [Freund (2020)](https://techcommunity.microsoft.com/blog/adforpostgresql/analyzing-the-limits-of-connection-scalability-in-postgres/1757266); [Brandur (2018)](https://brandur.org/postgres-connections); [Măciucă et al. (2013)](https://scientificbulletin.upb.ro/static/pdfs/rez3bb_114891.pdf); [Sobri et al. (2022)](https://doi.org/10.24191/jeesr.v20i1.004) | Aplicada e medida | 1,68 → 6,85 | 41966,6 → 8820,5 | 96,4% → 99,8% | 399,9 → 402,8 MiB | 9,3% → 15,0% | [165605](resultados/20261109-165605-03-pool/resumo.txt), [165747](resultados/20261109-165747-03-pool/resumo.txt), [165931](resultados/20261109-165931-03-pool/resumo.txt) | O pool melhorou a vazão (de 6,27 para 6,85 req/s contra a mudança 02), o p95 (de 16796,6 para 8820,5 ms) e a CPU por requisição (de cerca de 16 para cerca de 15, conta feita dividindo a CPU média pela vazão), como eu esperava. Só que a mediana piorou (de 493,0 para 1490,5 ms), o que eu não esperava: as rotas leves ficaram cerca de 3 vezes mais lentas e as pesadas ficaram mais rápidas. Minha explicação, que eu não medi, é que o pool tem 10 conexões para 20 usuários: as consultas leves esperam na fila atrás das pesadas, e o limite de conexões alivia a disputa pela CPU do banco. Escolhi o `max` 10 sem considerar o número de usuários da carga (20), e esse resultado levou à mudança 04. |
| 04 | Pool com `max: 20`, igual ao número de usuários da carga (`api/src/db.js`, commit `92059e8`) | Com `max: 20`, igual ao número de usuários, as consultas leves não deverão mais esperar na fila do pool, e a mediana deve voltar perto da mudança 02; em compensação, o p95 deve subir, porque mais consultas pesadas disputam a CPU do banco ao mesmo tempo. Critério de equilíbrio: o melhor tamanho de pool é o que equilibra a mediana, o p95 e a vazão, sem melhorar uma à custa da outra. | [Sobri et al. (2022)](https://doi.org/10.24191/jeesr.v20i1.004); [Percona (Camargos, 2018)](https://www.percona.com/blog/2018/06/27/scaling-postgresql-with-pgbouncer-you-may-need-a-connection-pooler-sooner-than-you-expect/); IBM, *WebSphere Connection Pooling* (Erickson, Lauzon e Modjeski, ago. 2001), p. 12-13 e 40 (PDF que li; não achei página oficial da IBM) | Aplicada, sem ganho | 1,68 → 4,03 | 41966,6 → 24147,3 | 96,4% → 98,7% | 399,9 → 402,5 MiB | 9,3% → 15,5% | [171132](resultados/20261109-171132-04-pool-max20/resumo.txt), [171328](resultados/20261109-171328-04-pool-max20/resumo.txt), [171524](resultados/20261109-171524-04-pool-max20/resumo.txt) | Com 20 conexões, a mediana foi para 398,5 ms (a melhor de todas as etapas) e as rotas leves ficaram rápidas (a `cliente` em 105,1 ms), como eu esperava. O p95 subiu, mas mais do que eu previa: foi para 24147,3 ms, pior que o da mudança 02, sem pool (16796,6 ms). A vazão também caiu (4,03 req/s) e apareceram erros (0,32% em duas execuções), o que eu não esperava. Minha explicação, que eu não medi, é que, com 20 conexões, as consultas pesadas rodam juntas e disputam a única CPU do banco: cada uma demora mais, e os usuários ficam presos nelas e fazem menos requisições. A CPU por requisição piorou (de cerca de 15 para cerca de 25, dividindo a CPU média pela vazão). Pelo critério de equilíbrio, o `max` 10 se saiu melhor no conjunto, e o 20 só ganhou na mediana e nas rotas leves. |
| 05 | Índice multicoluna `(status, criado_em, id)` em `pedidos` (`banco/04-indexes-pedidos.sql`, commit `0c5c5f8`) | O índice vai reduzir o tempo da consulta do `/pedidos`: indexar as colunas juntas, numa rota com 15% do peso da carga e com 15000 páginas por status, pode dar um bom ganho de tempo. | [Índices multicoluna (PostgreSQL 16)](https://www.postgresql.org/docs/16/indexes-multicolumn.html); [Índices e ORDER BY (PostgreSQL 16)](https://www.postgresql.org/docs/16/indexes-ordering.html); [Winand, Top-N](https://use-the-index-luke.com/sql/partial-results/top-n-queries); Silberschatz cap. 23 (p. 596-598) | Aplicada e medida | 1,68 → 9,85 | 41966,6 → 7682,8 | 96,4% → 99,3% | 399,9 → 429,7 MiB | 9,3% → 19,7% | [010746](resultados/20261110-010746-05-indice-pedidos/resumo.txt), [010928](resultados/20261110-010928-05-indice-pedidos/resumo.txt), [011113](resultados/20261110-011113-05-indice-pedidos/resumo.txt) | Depois do índice, o tempo da consulta diminuiu: na página 1, o `EXPLAIN ANALYZE` foi de 389,5 para 0,9 ms, e a contagem de 204,0 para 47,3 ms ([diagnóstico 09](diagnostico-bd/09-explain-pedidos-por-status-com-indice.txt)). Na carga, a mediana da rota `pedidos-por-status` foi de 5637,4 para 1711,9 ms, e a vazão geral subiu de 6,85 para 9,85 req/s contra a mudança 03. O banco continua perto de 100% de CPU, então o ganho é de CPU por requisição (cerca de 15 na 03 contra cerca de 10 na 05, conta que eu fiz dividindo a CPU média pela vazão). O índice não ajuda em tudo: na página 15000 (`OFFSET` 299980) o banco continuou lendo a tabela inteira (1147,0 → 1104,9 ms), mas a carga só pede páginas de 1 a 1000, e nela o índice é usado (página 1000: 64,3 ms). |
| 06 | Rota `/relatorios/vendas-por-dia` agrupando e somando no SQL (`GROUP BY` com `count(DISTINCT)` e `sum`) no lugar de somar no JavaScript (`api/src/rotas.js`, commit `543243d`) | Agrupar no SQL vai reduzir o tempo da rota e possivelmente aumentar o uso da CPU. | [PostgreSQL 16, Aggregate Functions](https://www.postgresql.org/docs/16/tutorial-agg.html); [PostgreSQL 16, GROUP BY e HAVING](https://www.postgresql.org/docs/16/queries-table-expressions.html); [Supabase Wrappers, Query Pushdown](https://fdw.dev/guides/query-pushdown/); [Kossmann (2000)](https://doi.org/10.1145/371578.371598); Silberschatz cap. 23 (p. 598-599) | Aplicada e medida | 1,68 → 7,68 | 41966,6 → 8593,3 | 96,4% → 100,2% | 399,9 → 406,4 MiB | 9,3% → 4,6% | [025242](resultados/20261110-025242-06-intercalado/resumo.txt), [025701](resultados/20261110-025701-06-intercalado/resumo.txt), [030119](resultados/20261110-030119-06-intercalado/resumo.txt) | A rota `vendas-por-dia` ficou mais rápida: a mediana foi de 6283,1 para 2610,4 ms contra a mudança 05, medida na mesma ronda. A CPU da API caiu de 21,4% para 4,6%, porque o Node deixou de receber e somar cerca de 13 mil linhas. A CPU do banco não aumentou, como eu achava que poderia: ficou em 100,2% nas duas versões, porque o banco já estava no limite. O p95 geral caiu de 13428,9 para 8593,3 ms (as faixas das execuções não se sobrepõem). A vazão (7,29 → 7,68 req/s), o p99 e a mediana geral ficaram dentro do ruído. O ganho é modesto no geral, porque a rota tem 8% do peso da carga. As colunas de comparação com a linha de base vêm de sessões diferentes da máquina: veja a nota sobre a variação entre sessões. |
| 07 | Índice na data de `criado_em` (`(criado_em::date)`) em `pedidos` (`banco/05-indexes-vendas-por-dia.sql`, commit `01995f2`) | O tempo da requisição `vendas-por-dia` vai abaixar, porque agora a data de `criado_em` tem índice e o banco pode buscar diretamente pela data, sem precisar olhar todos os pedidos. Não deve ter uma grande baixa geral na API, porque é uma requisição com apenas 8% de peso na carga. | [Índices em expressões (PostgreSQL 16)](https://www.postgresql.org/docs/16/indexes-expressional.html) | Aplicada, sem ganho | 1,68 → 7,97 | 41966,6 → 8231,3 | 96,4% → 96,3% | 399,9 → 410,3 MiB | 9,3% → 4,4% | [181625](resultados/20261110-181625-07-indice-data/resumo.txt), [181810](resultados/20261110-181810-07-indice-data/resumo.txt), [181956](resultados/20261110-181956-07-indice-data/resumo.txt) | A hipótese se confirmou só em parte. A consulta sozinha ficou muito mais rápida: no `EXPLAIN`, foi de 393,8 para 18,7 ms, e o banco passou a usar o índice novo. Mas na carga a rota `vendas-por-dia` não ficou mais rápida: a mediana foi de 2905,2 ms, contra 2610,4 ms da mudança 06 (sessões diferentes, dentro da variação). A vazão geral também não mudou de forma mensurável (7,68 → 7,97 req/s), como eu esperava. O banco continua no limite de CPU, então a requisição passa a maior parte do tempo esperando a vez, e não executando a consulta (isso é uma explicação provável, não medi a espera). |
| 08 | Rota `/pedidos` respondendo só pelo índice: a consulta pede as 4 colunas usadas no lugar de `SELECT *` (`api/src/rotas.js`) e o índice da mudança 05 é trocado por um com `INCLUDE (cliente_id)` (`banco/06-indexes-pedidos-cobertura.sql`), commit `6c657a6` | O tempo que o banco passará na requisição será menor, dessa forma, podendo acarretar numa diminuição do uso da CPU. | [Index-Only Scans e Covering Indexes (PostgreSQL 16)](https://www.postgresql.org/docs/16/indexes-index-only-scans.html); [LIMIT e OFFSET (PostgreSQL 16)](https://www.postgresql.org/docs/16/queries-limit.html); [pg_stat_statements (PostgreSQL 16)](https://www.postgresql.org/docs/16/pgstatstatements.html) | Aplicada e medida | 1,68 → 13,42 | 41966,6 → 4259,7 | 96,4% → 99,4% | 399,9 → 410,7 MiB | 9,3% → 6,1% | [214706](resultados/20261111-214706-08-intercalado/resumo.txt), [215347](resultados/20261111-215347-08-intercalado/resumo.txt), [220043](resultados/20261111-220043-08-intercalado/resumo.txt) | A primeira parte da hipótese se confirmou: contra a mudança 07, medida na mesma ronda, a rota `pedidos-por-status` foi de 2140,0 para 1199,9 ms de mediana e de 18158,2 para 3005,1 ms de p95. A vazão geral subiu de 9,88 para 13,42 req/s e o p95 geral caiu de 9478,4 para 4259,7 ms (as faixas das execuções não se sobrepõem). A porcentagem de CPU do banco não caiu (97,9% → 99,4%): a carga não tem pausa entre as requisições, então o banco usou a folga para atender mais. O que caiu foi a CPU por requisição. As rotas `vendas-por-dia` e `top-produtos` ficaram mais lentas (veja as notas). |
| 09 | Rota `/relatorios/top-produtos` lendo de uma visão materializada (`receita_por_produto`, criada em `banco/07-top-produtos-materializada.sql`) no lugar de somar todos os itens a cada chamada (`api/src/rotas.js`), commit `76101e8` | O tempo da rota vai cair, assim como latência e métricas (p95 e p99). | [Materialized Views (PostgreSQL 16)](https://www.postgresql.org/docs/16/rules-materializedviews.html); [pg_stat_statements (PostgreSQL 16)](https://www.postgresql.org/docs/16/pgstatstatements.html) | Aplicada e medida | 1,68 → 40,70 | 41966,6 → 1125,8 | 96,4% → 99,3% | 399,9 → 481,7 MiB | 9,3% → 13,6% | [014420](resultados/20261112-014420-09-visao-materializada/resumo.txt), [014544](resultados/20261112-014544-09-visao-materializada/resumo.txt), [014711](resultados/20261112-014711-09-visao-materializada/resumo.txt) | A hipótese se confirmou. Contra a mudança 08, medida na mesma sessão (2 execuções de referência), a mediana da rota `top-produtos` saiu de 19487,5 e 27127,6 ms para 298,2 ms. O p95 geral foi de 5288,4 e 6652,4 ms para 1125,8 ms, e o p99 de 15929,1 e 26502,1 ms para 1507,3 ms. A vazão foi de 12,52 e 9,07 para 40,70 req/s. As outras rotas também ficaram mais rápidas, porque a `top-produtos` deixou de ocupar o banco por segundos a cada chamada. Custos: o resultado da visão fica desatualizado se os pedidos mudarem, e a memória do banco subiu para perto do limite do container (veja as notas). |
| 10 | Limites de CPU redistribuídos, com o mesmo total de 1,5 CPU: banco de 1,0 para 1,2 e API de 0,5 para 0,3 (`docker-compose.yml`, commit `2fe69c9`) | O tempo médio (aqui medido pela mediana geral) diminui e, provavelmente, as latências de cauda (p95 e p99) também. | Sem fonte externa: ideia minha, a partir do `recursos.csv` da mudança 09 (banco em ~99% de 1 CPU, API em 12% a 14%). | Aplicada e medida | 1,68 → 52,52 | 41966,6 → 897,3 | 96,4% → 118,4% | 399,9 → 185,1 MiB | 9,3% → 12,8% | [213149](resultados/20261113-213149-10-cpu-redistribuida/resumo.txt), [213316](resultados/20261113-213316-10-cpu-redistribuida/resumo.txt), [213446](resultados/20261113-213446-10-cpu-redistribuida/resumo.txt) | A hipótese se confirmou em parte. Contra 2 execuções da mudança 09 medidas no mesmo dia (limites antigos), a vazão foi de 44,02 e 45,99 para 52,52 req/s, a mediana geral de 394,8 e 314,5 para 299,5 ms e o p95 de 1081,3 e 1090,8 para 897,3 ms. O p99 não ficou claro: 1371,9 ms na mediana, contra 1678,9 e 1723,3, mas uma das 3 execuções deu 1774,4 ms, acima das duas referências. O banco passou a usar mais CPU (118,4%, com teto de 120%) e a API não travou. Detalhes e limites nas notas. |

Contrato: mantido nas 3 execuções de cada mudança (`contrato.txt` de cada pasta).

## Notas sobre a mudança 01

- Mediana do tempo de resposta geral: 2097,7 ms → 731,3 ms. p99: 46352,2 ms → 29905,6 ms.
- A variação entre execuções é grande (req/s depois: 3,93; 4,82; 3,91), e são só 3 execuções.
- O banco continua perto de 100% de CPU, então segue sendo o gargalo.
- A memória média da API na linha de base oscilou muito entre execuções (28,6; 72,8; 73,3 MiB), então não dá para tirar conclusão dela.
- Erros: 0,34% na execução 3 (uma requisição de `top-produtos` que estourou o limite). A linha de base também teve erro na execução 3 (0,78%).

## Notas sobre a mudança 02

Comparação direta com a mudança 01 (mediana das 3 execuções de cada):

| Métrica | Mudança 01 | Mudança 02 |
|---|---|---|
| Requisições por segundo | 3,93 | 6,27 |
| Tempo de resposta, mediana (ms) | 731,3 | 493,0 |
| p95 geral (ms) | 16433,0 | 16796,6 |
| p99 geral (ms) | 29905,6 | 29905,2 |
| Banco, CPU média | 98,5% | 100,1% |
| Rota `/clientes/:id/pedidos`, mediana (ms) | 7390,8 | 598,5 |
| Rota `/clientes/:id/pedidos`, p95 (ms) | 12434,2 | 1352,9 |
| Rota `/clientes/:id/pedidos`, requisições em 60 s | 59 | 93 |

- A latência da rota caiu muito, como a hipótese previa. O p95 geral ficou igual ao da mudança 01.
- O banco chegou ao limite de CPU (100,1%). A CPU total não diminuiu, mas a CPU por requisição caiu (conta feita a partir das medianas: cerca de 25 por req/s na mudança 01 e cerca de 16 na 02).
- A variação entre execuções foi pequena nesta mudança (req/s: 5,78; 6,27; 6,58). Erro: 0,22% em uma execução.

## Notas sobre as mudanças 03 e 04 (pool)

Comparação direta (mediana das 3 execuções de cada):

| Métrica | 02 (sem pool) | 03 (`max` 10) | 04 (`max` 20) |
|---|---|---|---|
| Requisições por segundo | 6,27 | 6,85 | 4,03 |
| Tempo de resposta, mediana (ms) | 493,0 | 1490,5 | 398,5 |
| p95 geral (ms) | 16796,6 | 8820,5 | 24147,3 |
| p99 geral (ms) | 29905,2 | 19819,1 | 38041,0 |
| Erros | 0% | 0% | 0,32% |
| Banco, CPU média | 100,1% | 99,8% | 98,7% |
| CPU do banco por req/s (conta feita a partir das medianas) | cerca de 16 | cerca de 15 | cerca de 25 |

Mediana por rota (ms):

| Rota | 02 | 03 | 04 |
|---|---|---|---|
| `cliente` | 295,7 | 901,2 | 105,1 |
| `cliente-por-email` | 302,3 | 817,7 | 195,5 |
| `pedidos-do-cliente` | 598,5 | 1853,1 | 500,0 |
| `pedidos-por-status` | 8312,6 | 5637,4 | 16896,8 |
| `vendas-por-dia` | 11328,8 | 6338,9 | 14759,1 |
| `top-produtos` | 29581,8 | 20736,8 | 51789,4 |

- O tamanho do pool troca uma coisa pela outra: o `max` menor protege as consultas pesadas (p95, vazão e erros melhores) e atrasa as leves, e o `max` maior faz o contrário.
- A explicação da fila de conexões e da disputa pela CPU do banco é uma hipótese, e não foi medida diretamente.
- Um valor intermediário (por exemplo 15) ou menor (por exemplo 5) não foi testado.
- **Versão final adotada: `max: 10`.** Pelo critério de equilíbrio, foi a que se saiu melhor no conjunto entre as duas testadas (vazão, p95, p99, erros e CPU por requisição), e perdeu só na mediana. O código final é o mesmo da mudança 03 (medida no commit `cebdf56`), por isso não foi medido de novo.

## Notas sobre a mudança 05 (índice no `/pedidos`)

Comparação direta com a mudança 03, que tem o mesmo código final do pool (mediana das 3 execuções de cada):

| Métrica | 03 | 05 |
|---|---|---|
| Requisições por segundo | 6,85 | 9,85 |
| Tempo de resposta, mediana (ms) | 1490,5 | 790,9 |
| p95 geral (ms) | 8820,5 | 7682,8 |
| p99 geral (ms) | 19819,1 | 15960,8 |
| Erros | 0% | 0% |
| Banco, CPU média | 99,8% | 99,3% |
| CPU do banco por req/s (conta feita a partir das medianas) | cerca de 15 | cerca de 10 |

Mediana por rota (ms):

| Rota | 03 | 05 |
|---|---|---|
| `cliente` | 901,2 | 506,8 |
| `cliente-por-email` | 817,7 | 486,7 |
| `pedidos-do-cliente` | 1853,1 | 993,2 |
| `pedidos-por-status` | 5637,4 | 1711,9 |
| `vendas-por-dia` | 6338,9 | 4674,4 |
| `top-produtos` | 20736,8 | 17458,6 |

`EXPLAIN (ANALYZE, BUFFERS)` do `/pedidos` com status `pago`, antes ([04](diagnostico-bd/04-explain-pedidos-por-status.txt)) e depois ([09](diagnostico-bd/09-explain-pedidos-por-status-com-indice.txt)), em `Execution Time`:

| Consulta | Antes (ms) | Depois (ms) | Como o banco lê (depois) |
|---|---|---|---|
| Contagem | 204,0 | 47,3 | Index Only Scan |
| Página 1 | 389,5 | 0,9 | Index Scan Backward |
| Página 1000 | não medido antes | 64,3 | Index Scan Backward |
| Página 15000 | 1147,0 | 1104,9 | Seq Scan (continua) |

- As outras rotas também ficaram mais rápidas, mesmo sem mudança nelas. Minha explicação, que eu não medi, é que o `/pedidos` ocupava muito do banco, que está no limite de CPU, e liberar esse tempo ajuda as demais.
- A memória do banco subiu cerca de 27 MiB (402,8 → 429,7 MiB, medianas). Não medi a causa; o índice novo é uma possibilidade.
- O índice acelera leituras e deixa mais lentas as escritas em `pedidos`. A carga só lê, então esse custo não aparece nas medições.
- A variação entre execuções foi de 9,46 a 10,77 req/s. Erros: 0% nas 3 execuções.
- Limite: o `OFFSET` fundo (página 15000) continua caro. A paginação por chave resolveria, mas mudaria o funcionamento da rota e pode quebrar o contrato. Fica para `proximos-testes.md`.
- **Nota posterior (variação entre sessões):** na mesma máquina, no dia seguinte, o mesmo código da 05 rendeu menos. Medi de novo o commit `2670beb` (`05-controle`, 3 execuções: 7,32 req/s, mediana 1203,0 ms e p95 10309,8 ms) e em uma ronda intercalada com a 06 (`05-intercalado`, 3 execuções: 7,29 req/s). Esses valores estão bem abaixo dos 9,85 req/s desta mudança, e perto dos 6,85 da mudança 03. Por isso **o ganho de vazão da 05 sobre a 03 (6,85 → 9,85) não é confiável**: as duas medições foram feitas em sessões diferentes. Não sei a causa da variação (não medi). O que continua sustentado é o `EXPLAIN` (página 1: 389,5 → 0,9 ms) e a queda da rota `pedidos-por-status` medida dentro de cada sessão. A lição para o resto do trabalho é comparar versões na mesma sessão, de preferência intercaladas.

## Notas sobre a mudança 06 (`vendas-por-dia` agrupado no SQL)

A comparação certa é a da **ronda intercalada**: uma medição da 05 (commit `2670beb`), uma da 06 (commit `543243d`), e assim por diante, 3 de cada, para que uma variação da máquina caia nas duas versões (mediana das 3 execuções de cada):

| Métrica | 05 (`05-intercalado`) | 06 (`06-intercalado`) |
|---|---|---|
| Requisições por segundo | 7,29 | 7,68 |
| Tempo de resposta, mediana (ms) | 986,7 | 905,2 |
| p95 geral (ms) | 13428,9 | 8593,3 |
| p99 geral (ms) | 23579,0 | 23566,0 |
| Erros | 0% | 0% |
| Banco, CPU média | 100,2% | 100,2% |
| API, CPU média | 21,4% | 4,6% |
| Banco, memória média (MiB) | 425,8 | 406,4 |
| CPU do banco por req/s (conta feita a partir das medianas) | cerca de 14 | cerca de 13 |
| Rota `vendas-por-dia`, mediana (ms) | 6283,1 | 2610,4 |
| Rota `vendas-por-dia`, p95 (ms) | 16432,7 | 7547,9 |
| Rota `pedidos-por-status`, mediana (ms) | 2285,5 | 2798,7 |

- Faixas das 3 execuções: vazão 7,19 a 7,75 (05) e 6,99 a 8,10 (06); p95 10645,5 a 13459,3 (05) e 7842,2 a 9985,6 (06). Só o p95 e a rota `vendas-por-dia` têm faixas separadas; o resto fica dentro do ruído, inclusive a `pedidos-por-status`, que eu não alterei.
- **Primeiras rodadas da 06** (`06-vendas-sql`, 6 execuções em 2 rodadas seguidas, antes do controle): 6,79 e 7,33 req/s (medianas de cada rodada). Pareciam muito piores que os 9,85 da 05 original, mas o controle (`05-controle`, mesmo código da 05, medido logo depois) deu 7,32 req/s. O que variou foi a máquina, e não a mudança.
- **Diagnóstico de custo no banco** (uma execução, salva em [10](diagnostico-bd/10-explain-vendas-por-dia-atual.txt) e [11](diagnostico-bd/11-explain-vendas-por-dia-agrupado.txt)): 420,2 ms com a consulta atual e 393,8 ms agrupando no SQL. Sem a coluna `observacoes`, o banco passou a usar o índice da mudança 05 como Index Only Scan. A diferença é pequena e vem de uma execução só.
- **Limite:** o filtro `criado_em::date` continua sem índice, e a leitura da tabela `pedidos` é a maior parte do tempo da consulta. Um índice na expressão (`criado_em::date`) é a próxima mudança candidata.
- **Sobre o trade-off de levar trabalho para o banco** (Kossmann, 2000): ele avisa que o servidor pode virar gargalo. Aqui o banco já estava no limite de CPU, e mesmo assim a vazão não piorou, porque a soma de 13 mil linhas em 7 grupos custa pouco perto da leitura que o banco já fazia.

## Notas sobre a mudança 07 (índice na data de `criado_em`)

A comparação com a 06 é entre **sessões diferentes da máquina** (a 06 foi medida na madrugada de 10/11 e a 07 no fim da tarde do mesmo dia), então diferenças pequenas não significam nada (mediana das 3 execuções de cada):

| Métrica | 06 (`06-intercalado`) | 07 (`07-indice-data`) |
|---|---|---|
| Requisições por segundo | 7,68 | 7,97 |
| Tempo de resposta, mediana (ms) | 905,2 | 811,2 |
| p95 geral (ms) | 8593,3 | 8231,3 |
| p99 geral (ms) | 23566,0 | 24730,3 |
| Erros | 0% | 0% |
| Banco, CPU média | 100,2% | 96,3% |
| API, CPU média | 4,6% | 4,4% |
| Banco, memória média (MiB) | 406,4 | 410,3 |
| Rota `vendas-por-dia`, mediana (ms) | 2610,4 | 2905,2 |
| Rota `vendas-por-dia`, p95 (ms) | 7547,9 | 10908,0 |

- Faixas das 3 execuções da 07: vazão 7,53 a 9,30 req/s; rota `vendas-por-dia`, mediana 2701,3 a 3492,8 ms. Erros: 0% nas 3 execuções.
- **Diagnóstico da consulta sozinha** (uma execução de cada, salvas em [11](diagnostico-bd/11-explain-vendas-por-dia-agrupado.txt) e [12](diagnostico-bd/12-explain-vendas-por-dia-com-indice-data.txt)): 393,8 ms antes e 18,7 ms com o índice. Antes, o banco percorria o índice da mudança 05 inteiro e descartava 165229 linhas por processo; com o índice novo, descarta 160 (os pedidos cancelados do período). O diagnóstico 11 usou uma versão de teste da consulta, um pouco diferente da que ficou no código; o filtro por data é o mesmo.
- **Por que a rota não melhorou na carga:** o `EXPLAIN` mede a consulta sozinha, com o banco livre. Na carga, 20 usuários disputam um banco com 1 CPU, que fica perto de 100%. A consulta leva milissegundos, mas a requisição leva segundos, porque espera atrás das outras (principalmente `top-produtos` e `pedidos-por-status`, as mais caras). Não medi a espera diretamente; é a explicação que bate com os números.
- **Medições refeitas:** uma primeira bateria da 07, feita logo depois de recriar o banco, deu uma vazão bem mais alta que esta. Testes de rascunho na mesma sessão (com e sem o índice, no mesmo banco) não mostraram diferença de vazão por causa do índice, então aquela vazão vinha do momento da máquina, e não da mudança. Descartei essa bateria e os rascunhos (não estão no repositório, por isso não cito os números) e medi de novo; esta é a bateria que vale.
- O índice ocupa espaço e deixa mais lentas as escritas em `pedidos`. A carga só lê, então esse custo não aparece nas medições.
- **Limite:** melhorar uma consulta isolada não melhora a rota enquanto o banco inteiro estiver ocupado. O próximo ganho deve vir das rotas que mais seguram o banco (`top-produtos` e o `OFFSET` fundo do `pedidos-por-status`), que ficam para `proximos-testes.md`.

## Notas sobre a mudança 08 (`pedidos-por-status` só pelo índice)

**Como cheguei nela.** Depois da mudança 07, a CPU do banco continuava no limite. Usei a extensão `pg_stat_statements` para ver quais consultas mais consumiam o banco nos 60 s da carga ([diagnóstico 13](diagnostico-bd/13-pg-stat-statements-na-carga.txt)): a consulta da página do `/pedidos` ficou com 52,2% do tempo total de execução, a `top-produtos` com 20,2% e a `vendas-por-dia` com 17,0%. O `EXPLAIN` dessa consulta ([diagnóstico 14](diagnostico-bd/14-explain-pedidos-por-status-paginas.txt)) mostrou que ela usava o índice da mudança 05, mas abria a tabela para cada pedido percorrido, por causa do `SELECT *`: na página 1000 eram 20.000 pedidos percorridos para devolver 20.

**O que mudou.** A resposta da rota só usa `id`, `cliente_id`, `status` e `criado_em`. A consulta passou a pedir só essas 4 colunas, e o índice passou a guardar o `cliente_id` junto (`INCLUDE`). Com as 4 colunas no índice, o banco responde sem abrir a tabela (index-only scan). O índice da mudança 05 foi substituído, porque o novo faz tudo o que ele fazia.

**A consulta sozinha** (uma execução de cada, [diagnóstico 14](diagnostico-bd/14-explain-pedidos-por-status-paginas.txt) e [diagnóstico 16](diagnostico-bd/16-explain-pedidos-por-status-so-indice.txt)):

| Página | Antes | Depois |
|---|---|---|
| 1 | 1,191 ms | 0,121 ms |
| 500 | 87,853 ms | 2,827 ms |
| 1000 | 129,154 ms | 5,068 ms |

Na página 1000, o plano foi de `Index Scan` para `Index Only Scan`, com `Heap Fetches: 0`, e os blocos de dados tocados caíram de 20.245 para 125.

**Na carga**, a comparação é a da ronda intercalada: uma medição da 07 (commit `9770ce1`), uma da 08 (commit `af89972`), e assim por diante, 3 de cada, com o banco recriado a cada troca (mediana das 3 execuções de cada):

| Métrica | 07 (`07-intercalado`) | 08 (`08-intercalado`) |
|---|---|---|
| Requisições por segundo | 9,88 | 13,42 |
| Tempo de resposta, mediana (ms) | 704,2 | 708,0 |
| p95 geral (ms) | 9478,4 | 4259,7 |
| p99 geral (ms) | 20036,8 | 17215,7 |
| Erros | 0% | 0% |
| Banco, CPU média | 97,9% | 99,4% |
| API, CPU média | 4,8% | 6,1% |
| Banco, memória média (MiB) | 411,2 | 410,7 |
| CPU do banco por req/s (conta feita a partir das medianas) | cerca de 9,9 | cerca de 7,4 |
| Rota `pedidos-por-status`, mediana (ms) | 2140,0 | 1199,9 |
| Rota `pedidos-por-status`, p95 (ms) | 18158,2 | 3005,1 |
| Rota `vendas-por-dia`, mediana (ms) | 2557,0 | 3397,7 |
| Rota `top-produtos`, mediana (ms) | 16439,2 | 18762,0 |

- Faixas das 3 execuções: vazão 8,81 a 10,03 (07) e 12,42 a 14,26 (08); p95 geral 7530,7 a 11556,9 (07) e 4005,9 a 4300,7 (08). As faixas não se sobrepõem, então a diferença não é variação da máquina.
- **Sobre a CPU:** a porcentagem do banco não caiu. A carga usa 20 usuários sem pausa entre as requisições (`carga/teste-carga.js`), então o banco fica perto de 100% enquanto for o gargalo, e o ganho aparece como mais requisições atendidas com a mesma CPU.
- **Efeito colateral:** a `vendas-por-dia` ficou mais lenta (faixas 1739,6 a 2985,1 ms na 07 e 3091,5 a 4569,4 ms na 08) e a mediana da `top-produtos` também subiu. Uma explicação provável, que não medi: com mais requisições passando por segundo, as consultas pesadas disputam o processador com mais concorrentes.
- **Custo:** o índice novo ocupa 21 MB, o mesmo tamanho do índice da mudança 05 que ele substituiu. A memória do banco não mudou. O índice deixa mais lentas as escritas em `pedidos`, e a carga só lê, então esse custo não aparece nas medições.
- **Limite:** o `OFFSET` continua. O banco ainda percorre os pedidos anteriores à página pedida, só que dentro do índice, e por isso o tempo ainda cresce com a página. A paginação por chave resolveria, mas não permite ir direto a uma página qualquer ([Winand](https://use-the-index-luke.com/sql/partial-results/fetch-next-page)), e a rota recebe `pagina=N`: mudaria o contrato. Fica para `proximos-testes.md`.
- **Lição:** o `EXPLAIN` da mudança 05 testou só a página 1, onde abrir a tabela custa pouco. A carga sorteia páginas de 1 a 1000. Testar também uma página distante teria mostrado o problema antes.
- **Uso de IA:** : Os comandos foram feitos com o Claude Code, seguindo a documentação citada.

## Notas sobre a mudança 09 (`top-produtos` com visão materializada)

**Como cheguei nela.** No [diagnóstico 13](diagnostico-bd/13-pg-stat-statements-na-carga.txt), a consulta da `top-produtos` tinha 20,2% do tempo de execução do banco com só 8 chamadas em 60 s. Ela somava os 1,5 milhão de itens de pedido a cada chamada ([diagnóstico 15](diagnostico-bd/15-explain-top-produtos-atual.txt)) para devolver sempre o mesmo resultado, porque os pedidos não mudam durante a carga.

**O que mudou.** A soma por produto passou a ser feita uma vez, na criação do banco, e fica guardada em uma visão materializada (`receita_por_produto`, 19206 linhas, 2048 kB). A rota só lê esse resultado, ordena e corta no limite pedido. A resposta é a mesma: o contrato foi mantido.

**A consulta sozinha** (uma execução de cada): 3640,515 ms antes ([diagnóstico 15](diagnostico-bd/15-explain-top-produtos-atual.txt)) e 4,487 ms depois ([diagnóstico 17](diagnostico-bd/17-explain-top-produtos-materializada.txt)).

**Na carga**, o antes oficial da mudança 09 são as 3 execuções da mudança 08 feitas em 11/11 (rótulo `08-intercalado`, medianas: 13,42 req/s, p95 geral 4259,7 ms, rota `top-produtos` 18762,0 ms, CPU do banco 99,4%, memória do banco 410,7 MiB; pastas na linha da 08 da tabela). Antes de medir a mudança 09, rodei a mudança 08 duas vezes no mesmo dia, só para ver como a máquina estava (commit `2073892`, rótulo `08-controle`: [013823](resultados/20261112-013823-08-controle/resumo.txt), [014008](resultados/20261112-014008-08-controle/resumo.txt)) e em seguida as 3 da 09 (commit `786d751`). Desta vez não alternei as versões. Nessas duas execuções a 08 deu vazão igual ou menor que a da medição oficial, então o ganho da 09 não vem do momento da máquina. A coluna da 09 é a mediana das 3 execuções:

| Métrica | 08 (`08-controle`, 2 execuções) | 09 (`09-visao-materializada`) |
|---|---|---|
| Requisições por segundo | 12,52 e 9,07 | 40,70 |
| Tempo de resposta, mediana (ms) | 698,1 e 807,9 | 400,8 |
| p95 geral (ms) | 5288,4 e 6652,4 | 1125,8 |
| p99 geral (ms) | 15929,1 e 26502,1 | 1507,3 |
| Erros | 0% | 0% |
| Banco, CPU média | 95,6% e 96,0% | 99,3% |
| API, CPU média | 7,7% e 5,1% | 13,6% |
| Banco, memória média (MiB) | 411,6 e 408,8 | 481,7 |
| CPU do banco por req/s (conta feita a partir dos valores acima) | cerca de 7,6 e 10,6 | cerca de 2,4 |
| Rota `top-produtos`, mediana (ms) | 19487,5 e 27127,6 | 298,2 |
| Rota `pedidos-por-status`, mediana (ms) | 1185,6 e 1298,3 | 802,7 |
| Rota `vendas-por-dia`, mediana (ms) | 4798,1 e 3848,6 | 995,5 |

- Faixas das 3 execuções da 09: vazão 37,64 a 41,17 req/s; p95 geral 1103,2 a 1202,0 ms; rota `top-produtos`, mediana 288,1 a 302,8 ms. A pior execução da 09 tem cerca de 3 vezes a vazão da melhor referência da 08, então a diferença não é variação da máquina.
- **Custo principal: o dado pode ficar velho.** A visão materializada é uma foto do momento em que foi criada. Se um pedido for criado, alterado ou cancelado, a rota continua devolvendo o resultado antigo até alguém rodar `REFRESH MATERIALIZED VIEW receita_por_produto`. Na carga do desafio os dados não mudam, por isso o contrato se mantém. Em um sistema com escritas seria preciso uma rotina de atualização, que não implementei nem medi.
- **Memória do banco perto do limite.** A média subiu de cerca de 410 para 481,7 MiB, e o pico chegou a 506,1 MiB, com limite de 512 MiB no container. Não houve erro, mas não há folga. Não medi a causa.
- **Sobre a CPU:** a porcentagem do banco continua perto de 100%, pelo mesmo motivo da mudança 08 (a carga não tem pausa). A CPU da API subiu de cerca de 5% a 8% para 13,6%, porque ela atende mais requisições; o limite dela é 0,5 CPU.
- **Outros custos:** 2048 kB de disco para a visão, e a soma de 1,5 milhão de itens passa a rodar uma vez na criação do banco.
- **Limite:** a rota ainda lê as 19206 linhas da visão e ordena a cada chamada. Um índice na visão, pela receita, evitaria isso; fica para `proximos-testes.md`.
- **Uso de IA:** Seguindo a documentação citada, apenas foi requisitado ao Claude Code para que executasse de forma ágil a seguinte query:
        CREATE MATERIALIZED VIEW receita_por_produto AS
        SELECT pr.id, pr.nome, pr.categoria,
            sum(i.quantidade) AS unidades,
            sum(i.quantidade * i.preco_unitario_centavos) AS receita_centavos
        FROM itens_pedido i
        JOIN pedidos p ON p.id = i.pedido_id
        JOIN produtos pr ON pr.id = i.produto_id
        WHERE p.status <> 'cancelado'
        GROUP BY pr.id, pr.nome, pr.categoria;

## Notas sobre a mudança 10 (CPU redistribuída entre banco e API)

**Como cheguei nela.** No `recursos.csv` da mudança 09, o banco ficava perto de 99% de 1 CPU e a API em 12% a 14%, com picos de até 23,7%. A ideia foi tirar CPU da API, que sobrava, e dar ao banco, que era o gargalo, sem aumentar o total (1,5 CPU).

**O que mudou.** Só o `docker-compose.yml`: banco de `cpus: "1.0"` para `"1.2"` e API de `"0.5"` para `"0.3"`. O código e o banco não mudaram. O contrato foi mantido nas 5 execuções.

**Na carga.** O antes são 2 execuções da mudança 09 com os limites antigos, medidas no mesmo dia (rótulo `09-controle`: [212823](resultados/20261113-212823-09-controle/resumo.txt), [212953](resultados/20261113-212953-09-controle/resumo.txt)). Como são só 2, mostro os dois valores. A coluna da 10 é a mediana das 3 execuções (rótulo `10-cpu-redistribuida`).

| Métrica | 09 (`09-controle`, 2 execuções) | 10 (`10-cpu-redistribuida`) |
|---|---|---|
| Requisições por segundo | 44,02 e 45,99 | 52,52 |
| Tempo de resposta, mediana (ms) | 394,8 e 314,5 | 299,5 |
| p95 geral (ms) | 1081,3 e 1090,8 | 897,3 |
| p99 geral (ms) | 1678,9 e 1723,3 | 1371,9 |
| Erros | 0% | 0% |
| Banco, CPU média | 99,3% e 93,4% | 118,4% |
| API, CPU média | 13,0% e 10,7% | 12,8% |
| Banco, memória média (MiB) | 445,4 e 485,2 | 185,1 |
| CPU do banco por req/s (conta feita a partir dos valores acima) | cerca de 2,3 e 2,0 | cerca de 2,3 |
| Rota `pedidos-por-status`, mediana (ms) | 697,8 e 697,8 | 594,6 |
| Rota `vendas-por-dia`, mediana (ms) | 794,2 e 802,4 | 696,4 |
| Rota `pedidos-do-cliente`, mediana (ms) | 401,6 e 395,2 | 301,8 |
| Rota `top-produtos`, mediana (ms) | 204,0 e 204,7 | 204,3 |

- Faixas: vazão das 3 execuções da 10 de 52,23 a 54,18 req/s, contra 44,02 e 45,99 da referência. As faixas não se sobrepõem, mas são poucas amostras e a variação entre execuções já passou de 30% em outras mudanças.
- **p99:** a hipótese não fica confirmada para o p99. A execução 2 da 10 deu 1774,4 ms, acima das duas referências.
- **A CPU por requisição não mudou** (cerca de 2,3 nos dois casos, conta feita dividindo a CPU média do banco pela vazão). Ou seja, o ganho de vazão vem de o banco ter mais CPU disponível, e não de cada requisição gastar menos.
- **A API não travou, mas chegou ao teto.** Pelo `recursos.csv`, a média da API ficou em 11,7% a 15,2% e o máximo foi 19,4% e 18,2% nas execuções 2 e 3. Na execução 1 houve um ponto de 33,0%, acima do teto de 30%, e 2 pontos acima de 28%. Foi pontual, sem ficar encostada no teto. Não sei dizer se esse pico atrasou alguma resposta.
- **Custo:** nenhum recurso a mais (o total continua 1,5 CPU), mas a API tem menos folga: o teto dela caiu de 50% para 30% de 1 CPU.
- **Memória do banco:** 185,1 MiB na 10 contra 445,4 e 485,2 MiB na referência. Não sei explicar a diferença e não verifiquei a causa. Não uso esse número como ganho.
- **Limite:** são só 2 execuções de referência e 3 da mudança, todas no mesmo dia. Uma máquina diferente ou outro dia podem dar outro resultado.
- **Uso de IA:** o Claude Code conferiu o contrato; os números vêm do `medir.sh`.
