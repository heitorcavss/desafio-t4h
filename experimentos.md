# Experimentos

Uma linha por ideia aplicada. Todo número de antes e depois vem do `scripts/medir.sh` (pastas em `resultados/`), e cada valor é a **mediana das 3 execuções**. Parâmetros iguais em todas as medições: 20 usuários virtuais, 60 s, semente 42.

**Antes usado:** a linha de base (aplicação original), nas 3 pastas abaixo. Cada mudança da tabela é comparada com ela. A mudança 02 também é comparada com a mudança 01, as mudanças 03 e 04 com a 02, a mudança 05 com a 03 (código final do pool, `max` 10) e a mudança 06 com a 05 (em uma ronda intercalada, nas mesmas condições da máquina), para isolar o efeito de cada uma (veja as notas).

- Linha de base: [171102](resultados/20261104-171102-00-linha-de-base/resumo.txt), [171309](resultados/20261104-171309-00-linha-de-base/resumo.txt), [171510](resultados/20261104-171510-00-linha-de-base/resumo.txt) (commit medido: `8134893`)

## Resultados

| # | Mudança | Hipótese | Fonte | Status | req/s | p95 (ms) | CPU banco | Memória banco | CPU API | Pastas (depois) | Conclusão |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 | Índices em `pedidos.cliente_id`, `itens_pedido.pedido_id` e `lower(email)` (`banco/03-indexes.sql`, commit `2b6901a`) | Criar índices nas colunas que as rotas filtram (`pedidos.cliente_id`, `itens_pedido.pedido_id` e `lower(email)`) deve reduzir o tempo das consultas e a CPU do banco, porque o banco deixa de ler as tabelas inteiras (Seq Scan) e descartar quase todas as linhas. | [Índices (PostgreSQL 16)](https://www.postgresql.org/docs/16/indexes-intro.html), [índices sobre expressões](https://www.postgresql.org/docs/16/indexes-expressional.html), Silberschatz cap. 23 (p. 596) | Aplicada e medida | 1,68 → 3,93 | 41966,6 → 16433,0 | 96,4% → 98,5% | 399,9 → 398,8 MiB | 9,3% → 15,5% | [024453](resultados/20261109-024453-01-indices/resumo.txt), [024643](resultados/20261109-024643-01-indices/resumo.txt), [024823](resultados/20261109-024823-01-indices/resumo.txt) | Depois dos índices, a latência diminuiu bastante e as requisições por segundo aumentaram, por conta da velocidade das consultas. Um comportamento esperado, porém não pensado, foi o aumento da CPU: ele vem do aumento de requisições por segundo, e significa que as consultas ficaram mais baratas (cada uma gasta menos CPU). A CPU da própria API também subiu, porque, com mais requisições por segundo, ela é mais utilizada. (A do banco subiu pouco, de 96,4% para 98,5%, porque já estava perto do limite.) |
| 02 | Rota `/clientes/:id/pedidos` com um `JOIN` no lugar das consultas em loop (`api/src/rotas.js`, commit `8ce1978`) | Ao alterar a rota `/clientes/:id/pedidos` provavelmente diminuirá o tempo de latência da rota específica, pois diminuirá o número de consultas e, por consequência, o de conexões ao banco de dados. Dessa forma, podendo acarretar em uma diminuição no uso da CPU, visto que a rota ficará mais responsiva. | Wellhausen (2008), "Object Prefetch Filter" [link pendente]; [Phabricator, N+1](https://secure.phabricator.com/book/phabcontrib/article/n_plus_one/); [OpenReplay, N+1](https://blog.openreplay.com/n-1-query-problem/); Silberschatz cap. 23 (p. 598-599) | Aplicada e medida | 1,68 → 6,27 | 41966,6 → 16796,6 | 96,4% → 100,1% | 399,9 → 403,5 MiB | 9,3% → 15,0% | [162701](resultados/20261109-162701-02-join/resumo.txt), [162849](resultados/20261109-162849-02-join/resumo.txt), [163030](resultados/20261109-163030-02-join/resumo.txt) | Depois do JOIN, a latência da rota `/clientes/:id/pedidos` diminuiu muito (a mediana foi de 7390,8 para 598,5 ms), porque ela deixou de fazer várias consultas e passou a fazer duas (no cliente 42, pela contagem do código; as conexões eu não medi diretamente). As requisições por segundo aumentaram (de 3,93 para 6,27), porque a rota ficou mais rápida. Só que a CPU não diminuiu como eu tinha pensado: o banco chegou ao limite (100,1%), porque, com mais requisições por segundo, ele continua trabalhando no máximo. O que diminuiu foi a CPU por requisição: o banco gasta menos CPU para atender cada uma (cerca de 25 por req/s na mudança 01 contra cerca de 16 na 02). Essa é uma conta que eu fiz, dividindo a CPU média pela vazão, e não um número do `medir.sh`. O p95 geral ficou igual (16433,0 → 16796,6 ms), porque os tempos mais lentos agora vêm de outras rotas, que eu não mexi. |
| 03 | Pool de conexões no lugar de uma conexão por consulta, com `max: 10` (`api/src/db.js`, commit `cebdf56`) | A implementação do pool pode acarretar a diminuição do tempo de latência geral da API, visto que o tempo para abrir uma conexão nova é consideravelmente maior do que o de reaproveitar uma conexão já aberta, implicando diretamente nas requisições por segundo e na diminuição do custo de CPU de uma requisição única, ou seja, mais req/s. | [node-postgres, Pooling](https://node-postgres.com/features/pooling); [Percona (Camargos, 2018)](https://www.percona.com/blog/2018/06/27/scaling-postgresql-with-pgbouncer-you-may-need-a-connection-pooler-sooner-than-you-expect/); [Freund (2020)](https://techcommunity.microsoft.com/blog/adforpostgresql/analyzing-the-limits-of-connection-scalability-in-postgres/1757266); [Brandur (2018)](https://brandur.org/postgres-connections); Măciucă et al. (2013) [link pendente]; [Sobri et al. (2022)](https://doi.org/10.24191/jeesr.v20i1.004) | Aplicada e medida | 1,68 → 6,85 | 41966,6 → 8820,5 | 96,4% → 99,8% | 399,9 → 402,8 MiB | 9,3% → 15,0% | [165605](resultados/20261109-165605-03-pool/resumo.txt), [165747](resultados/20261109-165747-03-pool/resumo.txt), [165931](resultados/20261109-165931-03-pool/resumo.txt) | O pool melhorou a vazão (de 6,27 para 6,85 req/s contra a mudança 02), o p95 (de 16796,6 para 8820,5 ms) e a CPU por requisição (de cerca de 16 para cerca de 15, conta feita dividindo a CPU média pela vazão), como eu esperava. Só que a mediana piorou (de 493,0 para 1490,5 ms), o que eu não esperava: as rotas leves ficaram cerca de 3 vezes mais lentas e as pesadas ficaram mais rápidas. Minha explicação, que eu não medi, é que o pool tem 10 conexões para 20 usuários: as consultas leves esperam na fila atrás das pesadas, e o limite de conexões alivia a disputa pela CPU do banco. Escolhi o `max` 10 sem considerar o número de usuários da carga (20), e esse resultado levou à mudança 04. |
| 04 | Pool com `max: 20`, igual ao número de usuários da carga (`api/src/db.js`, commit `92059e8`) | Com `max: 20`, igual ao número de usuários, as consultas leves não deverão mais esperar na fila do pool, e a mediana deve voltar perto da mudança 02; em compensação, o p95 deve subir, porque mais consultas pesadas disputam a CPU do banco ao mesmo tempo. Critério de equilíbrio: o melhor tamanho de pool é o que equilibra a mediana, o p95 e a vazão, sem melhorar uma à custa da outra. | [Sobri et al. (2022)](https://doi.org/10.24191/jeesr.v20i1.004); [Percona (Camargos, 2018)](https://www.percona.com/blog/2018/06/27/scaling-postgresql-with-pgbouncer-you-may-need-a-connection-pooler-sooner-than-you-expect/); IBM, *WebSphere Connection Pooling* (2001), p. 12-13 e 40 [link pendente] | Aplicada e medida | 1,68 → 4,03 | 41966,6 → 24147,3 | 96,4% → 98,7% | 399,9 → 402,5 MiB | 9,3% → 15,5% | [171132](resultados/20261109-171132-04-pool-max20/resumo.txt), [171328](resultados/20261109-171328-04-pool-max20/resumo.txt), [171524](resultados/20261109-171524-04-pool-max20/resumo.txt) | Com 20 conexões, a mediana foi para 398,5 ms (a melhor de todas as etapas) e as rotas leves ficaram rápidas (a `cliente` em 105,1 ms), como eu esperava. O p95 subiu, mas mais do que eu previa: foi para 24147,3 ms, pior que o da mudança 02, sem pool (16796,6 ms). A vazão também caiu (4,03 req/s) e apareceram erros (0,32% em duas execuções), o que eu não esperava. Minha explicação, que eu não medi, é que, com 20 conexões, as consultas pesadas rodam juntas e disputam a única CPU do banco: cada uma demora mais, e os usuários ficam presos nelas e fazem menos requisições. A CPU por requisição piorou (de cerca de 15 para cerca de 25, dividindo a CPU média pela vazão). Pelo critério de equilíbrio, o `max` 10 se saiu melhor no conjunto, e o 20 só ganhou na mediana e nas rotas leves. |
| 05 | Índice multicoluna `(status, criado_em, id)` em `pedidos` (`banco/04-indexes-pedidos.sql`, commit `0c5c5f8`) | O índice vai reduzir o tempo da consulta do `/pedidos`: indexar as colunas juntas, numa rota com 15% do peso da carga e com 15000 páginas por status, pode dar um bom ganho de tempo. | [Índices multicoluna (PostgreSQL 16)](https://www.postgresql.org/docs/16/indexes-multicolumn.html); [Índices e ORDER BY (PostgreSQL 16)](https://www.postgresql.org/docs/16/indexes-ordering.html); [Winand, Top-N](https://use-the-index-luke.com/sql/partial-results/top-n-queries); Silberschatz cap. 23 (p. 596-598) | Aplicada e medida | 1,68 → 9,85 | 41966,6 → 7682,8 | 96,4% → 99,3% | 399,9 → 429,7 MiB | 9,3% → 19,7% | [010746](resultados/20261110-010746-05-indice-pedidos/resumo.txt), [010928](resultados/20261110-010928-05-indice-pedidos/resumo.txt), [011113](resultados/20261110-011113-05-indice-pedidos/resumo.txt) | Depois do índice, o tempo da consulta diminuiu: na página 1, o `EXPLAIN ANALYZE` foi de 389,5 para 0,9 ms, e a contagem de 204,0 para 47,3 ms ([diagnóstico 09](diagnostico-bd/09-explain-pedidos-por-status-com-indice.txt)). Na carga, a mediana da rota `pedidos-por-status` foi de 5637,4 para 1711,9 ms, e a vazão geral subiu de 6,85 para 9,85 req/s contra a mudança 03. O banco continua perto de 100% de CPU, então o ganho é de CPU por requisição (cerca de 15 na 03 contra cerca de 10 na 05, conta que eu fiz dividindo a CPU média pela vazão). O índice não ajuda em tudo: na página 15000 (`OFFSET` 299980) o banco continuou lendo a tabela inteira (1147,0 → 1104,9 ms), mas a carga só pede páginas de 1 a 1000, e nela o índice é usado (página 1000: 64,3 ms). |
| 06 | Rota `/relatorios/vendas-por-dia` agrupando e somando no SQL (`GROUP BY` com `count(DISTINCT)` e `sum`) no lugar de somar no JavaScript (`api/src/rotas.js`, commit `543243d`) | Agrupar no SQL vai reduzir o tempo da rota e possivelmente aumentar o uso da CPU. | [PostgreSQL 16, Aggregate Functions](https://www.postgresql.org/docs/16/tutorial-agg.html); [PostgreSQL 16, GROUP BY e HAVING](https://www.postgresql.org/docs/16/queries-table-expressions.html); [Supabase Wrappers, Query Pushdown](https://fdw.dev/guides/query-pushdown/); [Kossmann (2000)](https://doi.org/10.1145/371578.371598); Silberschatz cap. 23 (p. 598-599) | Aplicada e medida | 1,68 → 7,68 | 41966,6 → 8593,3 | 96,4% → 100,2% | 399,9 → 406,4 MiB | 9,3% → 4,6% | [025242](resultados/20261110-025242-06-intercalado/resumo.txt), [025701](resultados/20261110-025701-06-intercalado/resumo.txt), [030119](resultados/20261110-030119-06-intercalado/resumo.txt) | A rota `vendas-por-dia` ficou mais rápida: a mediana foi de 6283,1 para 2610,4 ms contra a mudança 05, medida na mesma ronda. A CPU da API caiu de 21,4% para 4,6%, porque o Node deixou de receber e somar cerca de 13 mil linhas. A CPU do banco não aumentou, como eu achava que poderia: ficou em 100,2% nas duas versões, porque o banco já estava no limite. O p95 geral caiu de 13428,9 para 8593,3 ms (as faixas das execuções não se sobrepõem). A vazão (7,29 → 7,68 req/s), o p99 e a mediana geral ficaram dentro do ruído. O ganho é modesto no geral, porque a rota tem 8% do peso da carga. As colunas de comparação com a linha de base vêm de sessões diferentes da máquina: veja a nota sobre a variação entre sessões. |

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
