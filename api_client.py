"""
Cliente HTTP alternativo para automação Degustone
Tenta realizar scraping via requisições HTTP diretas (sem navegador)
"""
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from pathlib import Path
from config import DegustoneConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DegustoneAPIClient:
    """Cliente para interagir com Degustone via HTTP"""
    
    def __init__(self):
        self.config = DegustoneConfig
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def login(self):
        """Tenta realizar login via POST"""
        logger.info("Tentando login via HTTP...")
        
        # Primeiro, obter a página de login para pegar tokens CSRF se houver
        response = self.session.get(self.config.LOGIN_URL)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Procurar por token CSRF
        csrf_token = None
        csrf_input = soup.find('input', {'name': '_token'}) or soup.find('input', {'name': 'csrf_token'})
        if csrf_input:
            csrf_token = csrf_input.get('value')
            logger.info("Token CSRF encontrado")
        
        # Preparar dados de login
        login_data = {
            'cpf': self.config.CPF,
            'password': self.config.SENHA,
        }
        
        if csrf_token:
            login_data['_token'] = csrf_token
        
        # Tentar diferentes variações de nomes de campos
        for cpf_key, pwd_key in [
            ('cpf', 'password'),
            ('cpf', 'senha'),
            ('username', 'password'),
            ('login', 'password')
        ]:
            try:
                data = {
                    cpf_key: self.config.CPF,
                    pwd_key: self.config.SENHA
                }
                if csrf_token:
                    data['_token'] = csrf_token
                
                response = self.session.post(
                    self.config.LOGIN_URL,
                    data=data,
                    allow_redirects=True
                )
                
                # Verificar se login foi bem-sucedido
                if response.status_code == 200 and 'login' not in response.url.lower():
                    logger.info(f"Login bem-sucedido com campos: {cpf_key}/{pwd_key}")
                    return True
                    
            except Exception as e:
                logger.debug(f"Tentativa com {cpf_key}/{pwd_key} falhou: {e}")
                continue
        
        logger.warning("Não foi possível fazer login via HTTP direto")
        return False
    
    def select_franchise(self, franquia_id: str):
        """Seleciona servidor e franquia"""
        logger.info(f"Selecionando franquia {franquia_id}...")
        
        # Tentar POST para seleção
        selection_data = {
            'servidor': self.config.SERVIDOR_ID,
            'franquia': franquia_id
        }
        
        response = self.session.post(
            self.config.ACESSO_URL,
            data=selection_data,
            allow_redirects=True
        )
        
        return response.status_code == 200
    
    def get_report(self, franquia_id: str):
        """Obtém o relatório de despesas"""
        logger.info(f"Obtendo relatório para franquia {franquia_id}...")
        
        response = self.session.get(self.config.RELATORIO_URL)
        
        if response.status_code != 200:
            logger.error(f"Erro ao obter relatório: {response.status_code}")
            return None
        
        # Parse do HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extrair tabelas
        tables = soup.find_all('table')
        
        report_data = {
            'franquia_id': franquia_id,
            'timestamp': datetime.now().isoformat(),
            'html_content': str(soup),
            'tables_count': len(tables),
            'tables': []
        }
        
        # Extrair dados das tabelas
        for i, table in enumerate(tables):
            rows = table.find_all('tr')
            table_data = []
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_data = [cell.get_text(strip=True) for cell in cells]
                if row_data:
                    table_data.append(row_data)
            
            report_data['tables'].append({
                'table_index': i,
                'rows': table_data
            })
        
        return report_data
    
    def save_report(self, report_data: dict):
        """Salva o relatório"""
        output_dir = self.config.ensure_output_dir()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        franquia_id = report_data.get('franquia_id', 'unknown')
        
        # Salvar JSON
        json_path = output_dir / f'relatorio_http_franquia_{franquia_id}_{timestamp}.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Relatório salvo em: {json_path}")
        
        # Salvar HTML
        html_path = output_dir / f'relatorio_http_franquia_{franquia_id}_{timestamp}.html'
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(report_data.get('html_content', ''))
        
        return json_path
    
    def run(self, franquia_id: str = None):
        """Executa o processo completo"""
        try:
            self.config.validate()
            
            # Login
            if not self.login():
                raise Exception("Falha no login")
            
            # Processar franquias
            franquias = [franquia_id] if franquia_id else self.config.get_franquias_list()
            
            results = []
            for fid in franquias:
                logger.info(f"\nProcessando franquia: {fid}")
                
                try:
                    # Selecionar franquia
                    if not self.select_franchise(str(fid)):
                        raise Exception("Falha ao selecionar franquia")
                    
                    # Obter relatório
                    report_data = self.get_report(str(fid))
                    if not report_data:
                        raise Exception("Falha ao obter relatório")
                    
                    # Salvar
                    saved_path = self.save_report(report_data)
                    
                    results.append({
                        'franquia_id': fid,
                        'status': 'success',
                        'file': str(saved_path)
                    })
                    
                except Exception as e:
                    logger.error(f"Erro: {e}")
                    results.append({
                        'franquia_id': fid,
                        'status': 'error',
                        'error': str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Erro durante execução: {e}")
            raise


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cliente HTTP para Degustone')
    parser.add_argument('--franquia', type=str, help='ID da franquia')
    
    args = parser.parse_args()
    
    client = DegustoneAPIClient()
    results = client.run(franquia_id=args.franquia)
    
    # Resumo
    print("\n" + "="*50)
    print("RESUMO DA EXECUÇÃO (HTTP)")
    print("="*50)
    for result in results:
        print(f"\nFranquia {result['franquia_id']}: {result['status'].upper()}")
        if result['status'] == 'success':
            print(f"  Arquivo: {result['file']}")
        else:
            print(f"  Erro: {result.get('error', 'Desconhecido')}")


if __name__ == '__main__':
    main()
