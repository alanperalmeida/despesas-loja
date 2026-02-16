"""
Mini API para o n8n chamar o scraper e consolidacao via HTTP
Rode com: python api_server.py
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import subprocess
import threading
import os
import sys
import glob
from pathlib import Path
from datetime import datetime

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 5679

# Armazena status da ultima execucao
execution_status = {
    'running': False,
    'last_run': None,
    'last_result': None
}

class APIHandler(BaseHTTPRequestHandler):
    
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode('utf-8'))
    
    def do_GET(self):
        if self.path == '/status':
            self._send_json(execution_status)
        
        elif self.path == '/data':
            # Retorna o CSV consolidado como JSON
            csv_path = os.path.join(WORK_DIR, 'consolidado_despesas.csv')
            if not os.path.exists(csv_path):
                self._send_json({'error': 'CSV nao encontrado'}, 404)
                return
            
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                lines = f.read().strip().split('\n')
            
            if len(lines) < 2:
                self._send_json({'rows': [], 'total': 0})
                return
            
            headers = [h.strip() for h in lines[0].split(';')]
            rows = []
            for line in lines[1:]:
                cols = line.split(';')
                row = {}
                for i, h in enumerate(headers):
                    row[h] = cols[i].strip() if i < len(cols) else ''
                
                # Converter valor e sangria para numérico
                if row.get('valor'):
                    try:
                        row['valor_numerico'] = float(
                            row['valor'].replace('R$', '').replace('.', '').replace(',', '.').strip()
                        )
                    except:
                        row['valor_numerico'] = 0
                else:
                    row['valor_numerico'] = 0
                
                if row.get('sangria'):
                    try:
                        row['sangria_numerica'] = float(
                            row['sangria'].replace('R$', '').replace('.', '').replace(',', '.').strip()
                        )
                    except:
                        row['sangria_numerica'] = 0
                else:
                    row['sangria_numerica'] = 0
                
                row['data_carga'] = datetime.now().isoformat()
                rows.append(row)
            
            self._send_json({'rows': rows, 'total': len(rows)})
        
        elif self.path == '/health':
            self._send_json({'status': 'ok', 'timestamp': datetime.now().isoformat()})
        
        else:
            self._send_json({'error': 'Rota nao encontrada'}, 404)
    
    def do_POST(self):
        if self.path == '/scraper':
            if execution_status['running']:
                self._send_json({'error': 'Scraper ja esta rodando'}, 409)
                return
            
            execution_status['running'] = True
            execution_status['last_run'] = datetime.now().isoformat()
            
            try:
                # Rodar scraper
                result = subprocess.run(
                    [sys.executable, 'degustone_scraper.py', '--headless'],
                    cwd=WORK_DIR,
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                scraper_output = {
                    'step': 'scraper',
                    'returncode': result.returncode,
                    'stdout': result.stdout[-3000:] if result.stdout else '',
                    'stderr': result.stderr[-2000:] if result.stderr else ''
                }
                
                if result.returncode != 0:
                    execution_status['running'] = False
                    execution_status['last_result'] = scraper_output
                    self._send_json(scraper_output, 500)
                    return
                
                # Rodar consolidacao
                result2 = subprocess.run(
                    [sys.executable, 'consolidate_data.py'],
                    cwd=WORK_DIR,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                final_output = {
                    'step': 'completo',
                    'scraper': scraper_output,
                    'consolidacao': {
                        'returncode': result2.returncode,
                        'stdout': result2.stdout[-2000:] if result2.stdout else '',
                    },
                    'status': 'ok' if result2.returncode == 0 else 'erro_consolidacao'
                }
                
                execution_status['running'] = False
                execution_status['last_result'] = final_output
                self._send_json(final_output)
                
            except subprocess.TimeoutExpired:
                execution_status['running'] = False
                self._send_json({'error': 'Timeout (10 min)'}, 504)
            except Exception as e:
                execution_status['running'] = False
                self._send_json({'error': str(e)}, 500)
        
        else:
            self._send_json({'error': 'Rota nao encontrada'}, 404)
    
    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")


if __name__ == '__main__':
    print(f"=== API Degustone rodando em http://localhost:{PORT} ===")
    print(f"Diretorio: {WORK_DIR}")
    print(f"")
    print(f"Rotas disponiveis:")
    print(f"  POST /scraper  - Executa scraper + consolidacao")
    print(f"  GET  /data     - Retorna dados do CSV como JSON")
    print(f"  GET  /status   - Status da ultima execucao")
    print(f"  GET  /health   - Health check")
    print(f"")
    print(f"Aguardando requisicoes...")
    
    server = HTTPServer(('0.0.0.0', PORT), APIHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
        server.server_close()
