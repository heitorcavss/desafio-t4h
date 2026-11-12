# Próximos testes

Ideias que pesquisei e não testei. Nenhuma tem resultado medido. O que foi aplicado e medido está no [experimentos.md](experimentos.md).

1. **Diminuir a CPU da API.**
   Hipótese: a API usa menos CPU do que o limite dela, então dá para baixar o limite sem perder desempenho.

2. **Aumentar a CPU ou a memória do banco.**
   Hipótese: o banco atende mais req/s, porque ele é a parte que está no limite.
   Fonte: [Google Cloud SQL, otimizar o uso de CPU](https://docs.cloud.google.com/sql/docs/postgres/optimize-cpu-usage?hl=pt-br)

3. **Busca de produtos com `pg_trgm`.**
   Hipótese: a busca fica mais rápida, porque para de ler todos os produtos a cada chamada. O ganho geral deve ser pequeno.
   Fonte: [PostgreSQL 16, pg_trgm](https://www.postgresql.org/docs/16/pgtrgm.html)

4. **Índice na visão materializada da `top-produtos`.**
   Hipótese: a rota para de ordenar todas as linhas da visão a cada chamada. O ganho deve ser pequeno, porque ela já está rápida.
   Fonte: [PostgreSQL 16, Materialized Views](https://www.postgresql.org/docs/16/rules-materializedviews.html)

5. **Ajustar os parâmetros do PostgreSQL.**
   Hipótese: pode haver ganho em algum parâmetro, mas não há como estimar. A memória do banco já está no valor recomendado.
   Fonte: [Van Aken et al., SIGMOD 2017](https://www.cs.purdue.edu/homes/csjgwang/CloudNativeDB/OtterTuneSIGMOD17.pdf)
