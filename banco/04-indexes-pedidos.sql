-- Índice para GET /pedidos?status=&pagina=
-- O banco acha os pedidos do status já em ordem de data (e id), sem ordenar tudo.
CREATE INDEX pedidos_status_criado_em_id_idx ON pedidos (status, criado_em, id);
