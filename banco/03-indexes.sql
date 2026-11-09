CREATE INDEX pedidos_cliente_id_idx ON pedidos (cliente_id);
CREATE INDEX itens_pedido_pedido_id_idx ON itens_pedido (pedido_id);
CREATE INDEX clientes_email_lower_idx ON clientes (lower(email));

ANALYZE;