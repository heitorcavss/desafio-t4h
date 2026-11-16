# Próximos testes

Ideias que pesquisei e não apliquei. Nenhuma foi medida na carga. O que foi aplicado e medido está no [experimentos.md](experimentos.md).

1. **Índice comum em `produtos(nome)` para a busca.**
   Hipótese: a busca fica mais rápida em parte dos termos. No [diagnóstico 19](diagnostico-bd/19-explain-busca-indice-comum.txt), o banco usou o índice em 9 dos 12 termos da carga, mas só 4 ficaram claramente mais rápidos; em `teclado` e `webcam` ficou pior. Testei só o `EXPLAIN`, sem aplicar, porque o ganho na carga seria incerto.
   Como testaria: um `.sql` novo em `banco/` com o `CREATE INDEX`, recriar o banco, conferir o contrato e medir 3 vezes, contra 3 medições do mesmo dia sem o índice, olhando a rota `busca-produtos`.
   O que precisaria: só o arquivo `.sql` e recriar o banco (`docker compose down -v`). Sem CPU nem memória a mais; o índice ocupa um pouco de espaço em disco.
   Fonte: [PostgreSQL, Índices](https://www.postgresql.org/docs/16/indexes-intro.html)

2. **Índice na visão materializada da `top-produtos`.**
   Hipótese: a rota para de ordenar todas as linhas da visão a cada chamada. O ganho deve ser pequeno, porque ela já está rápida.
   Como testaria: um `.sql` novo com o índice na visão `receita_por_produto`, o `EXPLAIN` antes e depois salvo em `diagnostico-bd/`, e 3 medições contra 3 do mesmo dia sem o índice, olhando a rota `top-produtos`.
   O que precisaria: o arquivo `.sql` e recriar o banco. Como a rota tem 2% do peso da carga, o ganho geral tende a ficar dentro da variação entre execuções.
   Fonte: [PostgreSQL 16, Materialized Views](https://www.postgresql.org/docs/16/rules-materializedviews.html)

3. **Ajustar os parâmetros do PostgreSQL.**
   Hipótese: pode haver ganho em algum parâmetro, mas não há como estimar. A memória do banco já está no valor recomendado.
   Como testaria: um parâmetro por vez, no `command` do serviço `banco` do `docker-compose.yml`, aplicando com `docker compose up -d`, conferindo o contrato e medindo 3 vezes contra 3 do mesmo dia com o valor antigo.
   O que precisaria: ler a documentação de cada parâmetro antes de escolher o valor, e manter os de memória dentro do limite de 512 MB do container, para não passar do total de recursos.
   Fonte: [Van Aken et al., SIGMOD 2017](https://www.cs.purdue.edu/homes/csjgwang/CloudNativeDB/OtterTuneSIGMOD17.pdf)
