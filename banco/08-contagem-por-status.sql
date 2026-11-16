CREATE MATERIALIZED VIEW contagem_por_status AS
SELECT status, count(*) AS total
  FROM pedidos
 GROUP BY status;

ANALYZE contagem_por_status;


--foto dos dados. Se os pedidos mudarem, é preciso rodar
--   REFRESH MATERIALIZED VIEW contagem_por_status;
-- é vantagem pq os dados são armazenados em cache e não precisam ser recalculados a cada consulta.