-- ============================================
-- Tabela despesas_loja - VERSÃO SIMPLIFICADA
-- Execute este primeiro para testar
-- ============================================

-- Se já existir, apaga (CUIDADO: só use se for primeira instalação)
-- DROP TABLE IF EXISTS despesas_loja CASCADE;

-- Criar tabela
CREATE TABLE despesas_loja (
    id SERIAL PRIMARY KEY,
    
    -- Metadados da extração
    franquia_id VARCHAR(20) NOT NULL,
    franquia_nome VARCHAR(200),
    data_extracao TIMESTAMP,
    
    -- Colunas do relatório Degustone
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
    
    -- Valores numéricos
    valor_numerico NUMERIC(15,2),
    sangria_numerica NUMERIC(15,2),
    
    -- Campos adicionais (para preencher depois)
    categoria VARCHAR(100),
    centro_custo VARCHAR(100),
    aprovado BOOLEAN DEFAULT NULL,
    observacao TEXT,
    
    -- Auditoria
    tabela_origem VARCHAR(10),
    arquivo_origem VARCHAR(200),
    data_carga TIMESTAMP DEFAULT NOW(),
    
    -- Constraint único
    CONSTRAINT uk_despesa_unica UNIQUE (franquia_id, data_competencia, historico, valor)
);

-- Indices
CREATE INDEX idx_despesas_franquia ON despesas_loja(franquia_id);
CREATE INDEX idx_despesas_loja ON despesas_loja(loja);
CREATE INDEX idx_despesas_competencia ON despesas_loja(data_competencia);
CREATE INDEX idx_despesas_vencimento ON despesas_loja(data_vencimento);
CREATE INDEX idx_despesas_conta ON despesas_loja(conta);
CREATE INDEX idx_despesas_liquidado ON despesas_loja(liquidado);
CREATE INDEX idx_despesas_carga ON despesas_loja(data_carga);

-- Verificar se criou
SELECT 'Tabela criada com sucesso!' as mensagem;
SELECT COUNT(*) as total_registros FROM despesas_loja;
