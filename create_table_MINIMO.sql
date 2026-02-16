-- APENAS CRIAR A TABELA - VERSÃO MÍNIMA
-- Copie e execute ESTE BLOCO INTEIRO de uma vez

CREATE TABLE despesas_loja (
    id SERIAL PRIMARY KEY,
    franquia_id VARCHAR(20) NOT NULL,
    franquia_nome VARCHAR(200),
    data_extracao TIMESTAMP,
    loja VARCHAR(200),
    conferido VARCHAR(50),
    conta VARCHAR(200),
    historico TEXT,
    data_competencia VARCHAR(20),
    data_vencimento VARCHAR(20),
    liquidado VARCHAR(50),
    valor VARCHAR(50),
    sangria VARCHAR(50),
    n_cheque_pre VARCHAR(50),
    valor_numerico NUMERIC(15,2),
    sangria_numerica NUMERIC(15,2),
    categoria VARCHAR(100),
    centro_custo VARCHAR(100),
    aprovado BOOLEAN,
    observacao TEXT,
    tabela_origem VARCHAR(10),
    arquivo_origem VARCHAR(200),
    data_carga TIMESTAMP DEFAULT NOW()
);
