# Próximos testes

Ideias que pesquisei e não testei. Nenhuma tem resultado medido. O que foi aplicado e medido está no [experimentos.md](experimentos.md).

1. **Índice comum em `produtos(nome)` para a busca.**
   Hipótese: a busca fica mais rápida em parte dos termos. No [diagnóstico 19](diagnostico-bd/19-explain-busca-indice-comum.txt), o banco usou o índice em 9 dos 12 termos da carga, mas só 4 ficaram claramente mais rápidos; em `teclado` e `webcam` ficou pior. Testei só o `EXPLAIN`, sem aplicar, porque o ganho na carga seria incerto.
   Fonte: [PostgreSQL 16, Índices](https://www.postgresql.org/docs/16/indexes-intro.html)

2. **Índice na visão materializada da `top-produtos`.**
   Hipótese: a rota para de ordenar todas as linhas da visão a cada chamada. O ganho deve ser pequeno, porque ela já está rápida.
   Fonte: [PostgreSQL 16, Materialized Views](https://www.postgresql.org/docs/16/rules-materializedviews.html)

3. **Ajustar os parâmetros do PostgreSQL.**
   Hipótese: pode haver ganho em algum parâmetro, mas não há como estimar. A memória do banco já está no valor recomendado.
   Fonte: [Van Aken et al., SIGMOD 2017](https://www.cs.purdue.edu/homes/csjgwang/CloudNativeDB/OtterTuneSIGMOD17.pdf)
