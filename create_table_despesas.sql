-- ============================================
-- Tabela para armazenar despesas do Degustone
-- COM AS COLUNAS REAIS DO RELATÓRIO
-- ============================================

CREATE TABLE IF NOT EXISTS despesas_loja (
    -- Chave primária
    id SERIAL PRIMARY KEY,
    
    -- Metadados da extração
    franquia_id VARCHAR(20) NOT NULL,
    franquia_nome VARCHAR(200),
    data_extracao TIMESTAMP,
    
    -- ============================================
    -- COLUNAS DO RELATÓRIO DEGUSTONE (originais)
    -- ============================================
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
    
    -- Valores numéricos convertidos (para facilitar queries)
    valor_numerico NUMERIC(15,2),
    sangria_numerica NUMERIC(15,2),
    
    -- Campos adicionais para controle futuro (vazios inicialmente)
    categoria VARCHAR(100),
    centro_custo VARCHAR(100),
    aprovado BOOLEAN DEFAULT NULL,
    observacao TEXT,
    
    -- Metadados de auditoria
    tabela_origem VARCHAR(10),
    arquivo_origem VARCHAR(200),
    data_carga TIMESTAMP DEFAULT NOW(),
    
    -- Constraint para evitar duplicatas (ajustável conforme necessidade)
    -- Baseado em franquia + data_competencia + historico + valor
    CONSTRAINT uk_despesa_unica UNIQUE (franquia_id, data_competencia, historico, valor)
);

-- ============================================
-- Índices para otimizar consultas
-- ============================================
CREATE INDEX IF NOT EXISTS idx_despesas_franquia ON despesas_loja(franquia_id);
CREATE INDEX IF NOT EXISTS idx_despesas_loja ON despesas_loja(loja);
CREATE INDEX IF NOT EXISTS idx_despesas_competencia ON despesas_loja(data_competencia);
CREATE INDEX IF NOT EXISTS idx_despesas_vencimento ON despesas_loja(data_vencimento);
CREATE INDEX IF NOT EXISTS idx_despesas_conta ON despesas_loja(conta);
CREATE INDEX IF NOT EXISTS idx_despesas_liquidado ON despesas_loja(liquidado);
CREATE INDEX IF NOT EXISTS idx_despesas_carga ON despesas_loja(data_carga);

-- ============================================
-- Comentários nas colunas
-- ============================================
COMMENT ON TABLE despesas_loja IS 'Despesas extraídas do sistema Degustone via scraper automático';
COMMENT ON COLUMN despesas_loja.franquia_id IS 'ID da franquia (1866, 2610, 3127)';
COMMENT ON COLUMN despesas_loja.loja IS 'Nome da loja do relatório Degustone';
COMMENT ON COLUMN despesas_loja.conferido IS 'Status de conferência do lançamento';
COMMENT ON COLUMN despesas_loja.conta IS 'Conta contábil';
COMMENT ON COLUMN despesas_loja.historico IS 'Histórico/descrição da despesa';
COMMENT ON COLUMN despesas_loja.data_competencia IS 'Data de competência da despesa';
COMMENT ON COLUMN despesas_loja.data_vencimento IS 'Data de vencimento da despesa';
COMMENT ON COLUMN despesas_loja.liquidado IS 'Status de liquidação (pago/não pago)';
COMMENT ON COLUMN despesas_loja.valor IS 'Valor da despesa (texto original)';
COMMENT ON COLUMN despesas_loja.sangria IS 'Valor de sangria (texto original)';
COMMENT ON COLUMN despesas_loja.n_cheque_pre IS 'Número do cheque pré-datado';
COMMENT ON COLUMN despesas_loja.valor_numerico IS 'Valor convertido para decimal';
COMMENT ON COLUMN despesas_loja.sangria_numerica IS 'Sangria convertida para decimal';
COMMENT ON COLUMN despesas_loja.categoria IS 'Categoria customizada (preenchimento posterior)';
COMMENT ON COLUMN despesas_loja.centro_custo IS 'Centro de custo (preenchimento posterior)';
COMMENT ON COLUMN despesas_loja.aprovado IS 'Flag de aprovação (preenchimento posterior)';
COMMENT ON COLUMN despesas_loja.observacao IS 'Observações adicionais (preenchimento posterior)';
COMMENT ON COLUMN despesas_loja.data_carga IS 'Data/hora em que o registro foi inserido no banco';
