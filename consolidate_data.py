"""
Script de Consolidação de Dados para Banco de Dados (Versão Sem Dependências Externas)
Lê os arquivos JSON gerados pelo scraper e consolida em um formato CSV único.
"""
import json
import csv
import glob
import os
from pathlib import Path

def consolidate_reports(input_dir='./relatorios', output_file='consolidado_despesas.csv'):
    """
    Lê todos os JSONs de relatórios e consolida em um único arquivo CSV.
    Campos: franquia_id, franquia_nome, data_extracao, data_despesa, grupo, descricao, fornecedor, valor, tabela_origem
    """
    input_path = Path(input_dir)
    # Busca arquivos no padrao relatorio_*.json
    json_files = glob.glob(str(input_path / 'relatorio_*.json'))
    
    if not json_files:
        print(f"Nenhum arquivo JSON encontrado em {input_dir}")
        return

    print(f"Encontrados {len(json_files)} arquivos de relatórios.")
    
    # Definir colunas do CSV conforme estrutura real do Degustone
    csv_headers = [
        'franquia_id', 'franquia_nome', 'data_extracao',
        'loja', 'conferido', 'conta', 'historico',
        'data_competencia', 'data_vencimento', 'liquidado',
        'valor', 'sangria', 'n_cheque_pre',
        'tabela_origem', 'arquivo_origem'
    ]
    
    total_records = 0
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_headers, delimiter=';')
            writer.writeheader()
            
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Se for uma lista (formato antigo/debug), pega o primeiro item ou ignora
                    if isinstance(data, list):
                        if data: data = data[0]
                        else: continue

                    fid = data.get('franquia_id', '')
                    fname = data.get('franquia_nome', '')
                    timestamp = data.get('timestamp', '')
                    
                    tables = data.get('tables', [])
                    if not tables:
                        continue
                        
                    for table in tables:
                        headers = table.get('headers', [])
                        rows = table.get('rows', [])
                        
                        # Normalizar headers para lowercase
                        if headers and isinstance(headers[0], list):
                            headers = headers[0]
                        
                        # Pular tabelas sem headers ou com poucos headers (metadados)
                        if len(headers) < 5:
                            continue
                            
                        h_map = {h.lower().strip(): i for i, h in enumerate(headers)}
                        
                        # Mapear colunas REAIS do relatório Degustone
                        # Headers reais: Conferido, Conta, Histórico, D.Compet., D.Vencto., Liquidado, Valor, Sangria, Nº Cheque Pré
                        idx_conferido = h_map.get('conferido', -1)
                        idx_conta = h_map.get('conta', -1)
                        idx_historico = -1
                        for key in ['histórico', 'historico', 'hist.']:
                            if key in h_map:
                                idx_historico = h_map[key]
                                break
                        
                        idx_data_comp = -1
                        for key in ['d.compet.', 'data competência', 'data competencia', 'd.comp.', 'dt.compet.']:
                            if key in h_map:
                                idx_data_comp = h_map[key]
                                break
                        
                        idx_data_venc = -1
                        for key in ['d.vencto.', 'data vencimento', 'd.venc.', 'dt.vencto.']:
                            if key in h_map:
                                idx_data_venc = h_map[key]
                                break
                        
                        idx_liquidado = h_map.get('liquidado', -1)
                        idx_valor = h_map.get('valor', -1)
                        idx_sangria = h_map.get('sangria', -1)
                        
                        idx_cheque = -1
                        for key in ['nº cheque pré', 'n° cheque pré', 'n cheque pre', 'nº cheque pre', 'cheque']:
                            if key in h_map:
                                idx_cheque = h_map[key]
                                break
                        
                        # Extrair loja do contexto (linhas de cabeçalho da tabela)
                        loja_atual = ''

                        for row in rows:
                            # Detectar linha de loja:
                            # 1) Rows com apenas 1 elemento: ['ALCANTARA SHOPPING']
                            # 2) Rows onde só a primeira coluna tem valor
                            # MAS: ignorar datas (DD/MM/YYYY) que não são lojas
                            import re
                            is_single_value = False
                            if len(row) == 1 and row[0] and row[0].strip():
                                is_single_value = True
                            elif len(row) >= 2 and row[0] and row[0].strip() and not any(c for c in row[1:] if c and c.strip()):
                                is_single_value = True
                            
                            if is_single_value:
                                val = row[0].strip()
                                # Se for data (DD/MM/YYYY), NÃO é loja
                                if not re.match(r'^\d{2}/\d{2}/\d{4}$', val):
                                    loja_atual = val
                                continue
                            
                            # Pular linhas vazias ou de subtotal/total
                            first_val = (row[0] if row else '').strip().lower() if row else ''
                            if not first_val or first_val in ['total', 'subtotal', 'total geral'] or first_val.startswith('total '):
                                continue
                            
                            writer.writerow({
                                'franquia_id': fid,
                                'franquia_nome': fname,
                                'data_extracao': timestamp,
                                'loja': loja_atual,
                                'conferido': row[idx_conferido] if idx_conferido >= 0 and idx_conferido < len(row) else '',
                                'conta': row[idx_conta] if idx_conta >= 0 and idx_conta < len(row) else '',
                                'historico': row[idx_historico] if idx_historico >= 0 and idx_historico < len(row) else '',
                                'data_competencia': row[idx_data_comp] if idx_data_comp >= 0 and idx_data_comp < len(row) else '',
                                'data_vencimento': row[idx_data_venc] if idx_data_venc >= 0 and idx_data_venc < len(row) else '',
                                'liquidado': row[idx_liquidado] if idx_liquidado >= 0 and idx_liquidado < len(row) else '',
                                'valor': row[idx_valor] if idx_valor >= 0 and idx_valor < len(row) else '',
                                'sangria': row[idx_sangria] if idx_sangria >= 0 and idx_sangria < len(row) else '',
                                'n_cheque_pre': row[idx_cheque] if idx_cheque >= 0 and idx_cheque < len(row) else '',
                                'tabela_origem': table.get('table_index'),
                                'arquivo_origem': os.path.basename(json_file)
                            })
                            total_records += 1
                            
                except Exception as e:
                    print(f"Erro ao processar arquivo {json_file}: {e}")

        print("\n" + "="*50)
        print(f"Consolidação concluída com sucesso!")
        print(f"Arquivo gerado: {os.path.abspath(output_file)}")
        print(f"Total de registros processados: {total_records}")
        print("="*50)

    except Exception as e:
        print(f"Erro crítico ao criar CSV: {e}")

if __name__ == '__main__':
    consolidate_reports()
