import psycopg2
import sys

print("Conectando ao PostgreSQL...")
try:
    conn = psycopg2.connect(
        host='46.62.214.201',
        port=5432,
        dbname='n8n',
        user='postgres',
        password='78146702-324D-4466-9293-790E3723661C',
        connect_timeout=10
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    # Matar conexões exceto a atual
    sql = """
    SELECT pg_terminate_backend(pid) 
    FROM pg_stat_activity 
    WHERE datname = 'n8n' 
      AND pid <> pg_backend_pid()
    """
    
    cur.execute(sql)
    print(f"Comando executado. Conexoes encerradas: {cur.rowcount}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Erro: {e}")
