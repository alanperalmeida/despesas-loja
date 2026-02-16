"""
Importacao RAPIDA para PostgreSQL usando COPY (bulk load)
"""
import csv
import psycopg2
import sys
import io
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

DB_CONFIG = {
    'host': '46.62.214.201',
    'port': 5432,
    'dbname': 'n8n',
    'user': 'postgres',
    'password': '78146702-324D-4466-9293-790E3723661C',
    'connect_timeout': 15,
}

def parse_valor(v):
    if not v or not v.strip():
        return ''
    try:
        return str(float(v.replace('R$','').replace('.','').replace(',','.').strip()))
    except:
        return ''

def importar():
    print("Conectando...")
    sys.stdout.flush()
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("Conectado!")
    sys.stdout.flush()
    
    # Limpar tabela antes de reimportar (evita duplicatas)
    cur.execute("DELETE FROM despesas_loja")
    conn.commit()
    # Ler CSV
    print("Lendo CSV...")
    sys.stdout.flush()
    with open('consolidado_despesas.csv', 'r', encoding='utf-8-sig') as f:
        # Carregar tudo em memoria pois o arquivo fecha ao sair do bloco
        reader = list(csv.DictReader(f, delimiter=';'))
    
    # Filtrar registros validos e DEDUPLICAR
    print("Filtrando e deduplicando dados...")
    sys.stdout.flush()
    
    unique_keys = set()
    registros_unicos = []
    duplicatas = 0
    
    for r in reader:
        # Validacao basica: deve ter loja preenchida
        if not r.get('loja'):
            continue

        if not r.get('conta') and not r.get('historico'):
            continue
            
        # Chave unica: franquia_id + data_competencia + historico + valor
        # Normalizar para evitar duplicatas por espaco ou casing
        chave = (
            str(r.get('franquia_id', '')).strip(),
            str(r.get('data_competencia', '')).strip(),
            str(r.get('historico', '')).strip().lower().replace('\t', ' ').replace('\n', ' '),
            str(r.get('valor', '')).strip()
        )
        
        if chave in unique_keys:
            duplicatas += 1
            continue
        
        unique_keys.add(chave)
        registros_unicos.append(r)
        
    print(f"{len(registros_unicos)} registros unicos validos")
    print(f"{duplicatas} duplicatas ignoradas")
    sys.stdout.flush()
    
    # Montar buffer para COPY
    print("Preparando dados...")
    sys.stdout.flush()
    agora = datetime.now().isoformat()
    buf = io.StringIO()
    
    colunas = [
        'franquia_id','franquia_nome','data_extracao',
        'loja','conferido','conta','historico',
        'data_competencia','data_vencimento','liquidado',
        'valor','sangria','n_cheque_pre',
        'valor_numerico','sangria_numerica',
        'tabela_origem','arquivo_origem','data_carga'
    ]
    
    for row in registros_unicos:
        campos = [
            row.get('franquia_id',''),
            row.get('franquia_nome',''),
            row.get('data_extracao',''),
            row.get('loja',''),
            row.get('conferido',''),
            row.get('conta',''),
            row.get('historico','').replace('\t',' ').replace('\n',' '),
            row.get('data_competencia',''),
            row.get('data_vencimento',''),
            row.get('liquidado',''),
            row.get('valor',''),
            row.get('sangria',''),
            row.get('n_cheque_pre',''),
            parse_valor(row.get('valor','')),
            parse_valor(row.get('sangria','')),
            row.get('tabela_origem',''),
            row.get('arquivo_origem',''),
            agora,
        ]
        # Substituir vazio por \N (NULL do PostgreSQL)
        campos = [c if c else '\\N' for c in campos]
        buf.write('\t'.join(campos) + '\n')
    
    buf.seek(0)
    
    # COPY - envia tudo de uma vez
    print("Enviando para o banco (COPY)...")
    sys.stdout.flush()
    
    copy_sql = f"COPY despesas_loja ({','.join(colunas)}) FROM STDIN WITH (FORMAT text, NULL '\\N')"
    cur.copy_expert(copy_sql, buf)
    conn.commit()
    
    # Verificar
    cur.execute("SELECT COUNT(*) FROM despesas_loja")
    total = cur.fetchone()[0]
    
    print(f"\n=== RESULTADO ===")
    print(f"Total no banco: {total} registros")
    print("Importacao concluida!")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    importar()
