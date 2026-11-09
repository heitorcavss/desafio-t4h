const { Pool } = require('pg');

const config = {
  host: process.env.DB_HOST || 'localhost',
  port: Number(process.env.DB_PORT || 5432),
  user: process.env.DB_USER || 'loja',
  database: process.env.DB_NAME || 'loja',
  max: 10,
};

// Pool: as conexões ficam abertas e são reaproveitadas em vez de abrir uma por consulta.
// pool.query pega uma conexão, roda a consulta e devolve a conexão ao pool sozinho.
const pool = new Pool(config);

async function consultar(sql, parametros = []) {
  const resultado = await pool.query(sql, parametros);
  return resultado.rows;
}

module.exports = { consultar };
