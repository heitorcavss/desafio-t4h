DROP INDEX pedidos_status_criado_em_id_idx;
CREATE INDEX pedidos_status_criado_em_id_cliente_idx ON pedidos (status, criado_em, id) INCLUDE (cliente_id);

VACUUM ANALYZE pedidos;
