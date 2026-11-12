-- Visão materializada para GET /relatorios/top-produtos?limite=
-- Guarda, já somados, as unidades e a receita de cada produto (sem pedidos cancelados).
-- É a mesma consulta que a rota fazia a cada chamada, sem o ORDER BY e o LIMIT.
-- Atenção: é uma foto dos dados. Se os pedidos mudarem, é preciso rodar
--   REFRESH MATERIALIZED VIEW receita_por_produto;
CREATE MATERIALIZED VIEW receita_por_produto AS
SELECT pr.id, pr.nome, pr.categoria,
       sum(i.quantidade) AS unidades,
       sum(i.quantidade * i.preco_unitario_centavos) AS receita_centavos
  FROM itens_pedido i
  JOIN pedidos p ON p.id = i.pedido_id
  JOIN produtos pr ON pr.id = i.produto_id
 WHERE p.status <> 'cancelado'
 GROUP BY pr.id, pr.nome, pr.categoria;

ANALYZE receita_por_produto;
