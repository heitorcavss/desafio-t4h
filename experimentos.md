# Experimentos

Uma linha por ideia aplicada. Todo número de antes e depois vem do `scripts/medir.sh` (pastas em `resultados/`), e cada valor é a **mediana das 3 execuções**. Parâmetros iguais em todas as medições: 20 usuários virtuais, 60 s, semente 42.

**Antes usado:** a linha de base (aplicação original), nas 3 pastas abaixo. Cada mudança é comparada com ela, e não com a mudança anterior.

- Linha de base: [171102](resultados/20261104-171102-00-linha-de-base/resumo.txt), [171309](resultados/20261104-171309-00-linha-de-base/resumo.txt), [171510](resultados/20261104-171510-00-linha-de-base/resumo.txt) (commit medido: `8134893`)

## Resultados

| # | Mudança | Hipótese | Fonte | Status | req/s | p95 (ms) | CPU banco | Memória banco | CPU API | Pastas (depois) | Conclusão |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 | Índices em `pedidos.cliente_id`, `itens_pedido.pedido_id` e `lower(email)` (`banco/03-indexes.sql`, commit `2b6901a`) | Criar índices nas colunas que as rotas filtram (`pedidos.cliente_id`, `itens_pedido.pedido_id` e `lower(email)`) deve reduzir o tempo das consultas e a CPU do banco, porque o banco deixa de ler as tabelas inteiras (Seq Scan) e descartar quase todas as linhas. | [Índices (PostgreSQL 16)](https://www.postgresql.org/docs/16/indexes-intro.html), [índices sobre expressões](https://www.postgresql.org/docs/16/indexes-expressional.html), Silberschatz cap. 23 (p. 596) | Aplicada e medida | 1,68 → 3,93 | 41966,6 → 16433,0 | 96,4% → 98,5% | 399,9 → 398,8 MiB | 9,3% → 15,5% | [024453](resultados/20261109-024453-01-indices/resumo.txt), [024643](resultados/20261109-024643-01-indices/resumo.txt), [024823](resultados/20261109-024823-01-indices/resumo.txt) | Depois dos índices, a latência diminuiu bastante e as requisições por segundo aumentaram, por conta da velocidade das consultas. Um comportamento esperado, porém não pensado, foi o aumento da CPU: ele vem do aumento de requisições por segundo, e significa que as consultas ficaram mais baratas (cada uma gasta menos CPU). A CPU da própria API também subiu, porque, com mais requisições por segundo, ela é mais utilizada. (A do banco subiu pouco, de 96,4% para 98,5%, porque já estava perto do limite.) |

Contrato: mantido nas 3 execuções (`contrato.txt` de cada pasta).

## Notas sobre a mudança 01

- Mediana do tempo de resposta geral: 2097,7 ms → 731,3 ms. p99: 46352,2 ms → 29905,6 ms.
- A variação entre execuções é grande (req/s depois: 3,93; 4,82; 3,91), e são só 3 execuções.
- O banco continua perto de 100% de CPU, então segue sendo o gargalo.
- A memória média da API na linha de base oscilou muito entre execuções (28,6; 72,8; 73,3 MiB), então não dá para tirar conclusão dela.
- Erros: 0,34% na execução 3 (uma requisição de `top-produtos` que estourou o limite). A linha de base também teve erro na execução 3 (0,78%).
