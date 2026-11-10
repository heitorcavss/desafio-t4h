-- Índice para GET /relatorios/vendas-por-dia?inicio=&fim=
-- A rota filtra pelo dia do pedido (criado_em::date). Com os pedidos já em ordem de dia,
-- o banco vai direto ao período pedido, sem olhar todos os pedidos.
CREATE INDEX pedidos_criado_em_dia_idx ON pedidos ((criado_em::date));

-- Atualiza as estatísticas de pedidos, para o banco saber quantas linhas tem em cada dia.
ANALYZE pedidos;
