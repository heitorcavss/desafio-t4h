# Experimentos

Uma linha por ideia aplicada. Todo número de antes e depois vem do `scripts/medir.sh` (pastas em `resultados/`), e cada valor é a **mediana das 3 execuções**. Parâmetros iguais em todas as medições: 20 usuários virtuais, 60 s, semente 42.

**Antes usado:** a linha de base (aplicação original), nas 3 pastas abaixo. Cada mudança da tabela é comparada com ela. A mudança 02 também é comparada com a mudança 01, para isolar o efeito do `JOIN` (veja as notas).

- Linha de base: [171102](resultados/20261104-171102-00-linha-de-base/resumo.txt), [171309](resultados/20261104-171309-00-linha-de-base/resumo.txt), [171510](resultados/20261104-171510-00-linha-de-base/resumo.txt) (commit medido: `8134893`)

## Resultados

| # | Mudança | Hipótese | Fonte | Status | req/s | p95 (ms) | CPU banco | Memória banco | CPU API | Pastas (depois) | Conclusão |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 | Índices em `pedidos.cliente_id`, `itens_pedido.pedido_id` e `lower(email)` (`banco/03-indexes.sql`, commit `2b6901a`) | Criar índices nas colunas que as rotas filtram (`pedidos.cliente_id`, `itens_pedido.pedido_id` e `lower(email)`) deve reduzir o tempo das consultas e a CPU do banco, porque o banco deixa de ler as tabelas inteiras (Seq Scan) e descartar quase todas as linhas. | [Índices (PostgreSQL 16)](https://www.postgresql.org/docs/16/indexes-intro.html), [índices sobre expressões](https://www.postgresql.org/docs/16/indexes-expressional.html), Silberschatz cap. 23 (p. 596) | Aplicada e medida | 1,68 → 3,93 | 41966,6 → 16433,0 | 96,4% → 98,5% | 399,9 → 398,8 MiB | 9,3% → 15,5% | [024453](resultados/20261109-024453-01-indices/resumo.txt), [024643](resultados/20261109-024643-01-indices/resumo.txt), [024823](resultados/20261109-024823-01-indices/resumo.txt) | Depois dos índices, a latência diminuiu bastante e as requisições por segundo aumentaram, por conta da velocidade das consultas. Um comportamento esperado, porém não pensado, foi o aumento da CPU: ele vem do aumento de requisições por segundo, e significa que as consultas ficaram mais baratas (cada uma gasta menos CPU). A CPU da própria API também subiu, porque, com mais requisições por segundo, ela é mais utilizada. (A do banco subiu pouco, de 96,4% para 98,5%, porque já estava perto do limite.) |
| 02 | Rota `/clientes/:id/pedidos` com um `JOIN` no lugar das consultas em loop (`api/src/rotas.js`, commit `8ce1978`) | Ao alterar a rota `/clientes/:id/pedidos` provavelmente diminuirá o tempo de latência da rota específica, pois diminuirá o número de consultas e, por consequência, o de conexões ao banco de dados. Dessa forma, podendo acarretar em uma diminuição no uso da CPU, visto que a rota ficará mais responsiva. | Wellhausen (2008), "Object Prefetch Filter" [link pendente]; [Phabricator, N+1](https://secure.phabricator.com/book/phabcontrib/article/n_plus_one/); [OpenReplay, N+1](https://blog.openreplay.com/n-1-query-problem/); Silberschatz cap. 23 (p. 598-599) | Aplicada e medida | 1,68 → 6,27 | 41966,6 → 16796,6 | 96,4% → 100,1% | 399,9 → 403,5 MiB | 9,3% → 15,0% | [162701](resultados/20261109-162701-02-join/resumo.txt), [162849](resultados/20261109-162849-02-join/resumo.txt), [163030](resultados/20261109-163030-02-join/resumo.txt) | Depois do JOIN, a latência da rota `/clientes/:id/pedidos` diminuiu muito (a mediana foi de 7390,8 para 598,5 ms), porque ela deixou de fazer várias consultas e passou a fazer duas (no cliente 42, pela contagem do código; as conexões eu não medi diretamente). As requisições por segundo aumentaram (de 3,93 para 6,27), porque a rota ficou mais rápida. Só que a CPU não diminuiu como eu tinha pensado: o banco chegou ao limite (100,1%), porque, com mais requisições por segundo, ele continua trabalhando no máximo. O que diminuiu foi a CPU por requisição: o banco gasta menos CPU para atender cada uma (cerca de 25 por req/s na mudança 01 contra cerca de 16 na 02). Essa é uma conta que eu fiz, dividindo a CPU média pela vazão, e não um número do `medir.sh`. O p95 geral ficou igual (16433,0 → 16796,6 ms), porque os tempos mais lentos agora vêm de outras rotas, que eu não mexi. |

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
