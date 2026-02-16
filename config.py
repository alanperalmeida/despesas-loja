"""
Configurações para automação de extração de relatórios Degustone
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Carregar variáveis de ambiente
load_dotenv()

class DegustoneConfig:
    """Configurações centralizadas para o scraper Degustone"""
    
    # Credenciais
    CPF = os.getenv('DEGUSTONE_CPF', '14549094710')
    SENHA = os.getenv('DEGUSTONE_SENHA', '161097')
    
    # Servidor e Franquias
    SERVIDOR_ID = os.getenv('SERVIDOR_ID', '1')
    FRANQUIAS = os.getenv('FRANQUIAS', '1866,2610,3127').split(',')
    
    # Mapeamento de ID numerico -> nome exibido no dropdown do site
    # O site mostra nomes em vez de IDs no dropdown
    FRANQUIA_NOMES = {
        '1866': 'OFFICE NORTE SHOPPING',
        '2610': 'PANELA E TAL',
        '3127': 'BARDJECO',
    }
    
    # URLs
    BASE_URL = os.getenv('BASE_URL', 'https://degustone.com.br')
    LOGIN_URL = os.getenv('LOGIN_URL', f'{BASE_URL}/login')
    ACESSO_URL = os.getenv('ACESSO_URL', f'{BASE_URL}/acesso')
    RELATORIO_URL = os.getenv('RELATORIO_URL', f'{BASE_URL}/relatorio/despesas-loja')
    
    # Configurações de Scraping
    HEADLESS = os.getenv('HEADLESS', 'true').lower() == 'true'
    TIMEOUT = int(os.getenv('TIMEOUT', '30000'))
    RETRY_ATTEMPTS = int(os.getenv('RETRY_ATTEMPTS', '3'))
    
    # Diretórios
    OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR', './relatorios'))
    
    @classmethod
    def ensure_output_dir(cls):
        """Garante que o diretório de saída existe"""
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        return cls.OUTPUT_DIR
    
    @classmethod
    def get_franquias_list(cls):
        """Retorna lista de franquias como strings"""
        return [f.strip() for f in cls.FRANQUIAS]
    
    @classmethod
    def get_franquia_nome(cls, franquia_id: str):
        """Retorna o nome da franquia pelo ID"""
        return cls.FRANQUIA_NOMES.get(str(franquia_id), str(franquia_id))
    
    @classmethod
    def validate(cls):
        """Valida se as configurações essenciais estão presentes"""
        required = {
            'CPF': cls.CPF,
            'SENHA': cls.SENHA,
            'SERVIDOR_ID': cls.SERVIDOR_ID,
        }
        
        missing = [key for key, value in required.items() if not value]
        
        if missing:
            raise ValueError(f"Configurações obrigatórias ausentes: {', '.join(missing)}")
        
        return True

if __name__ == '__main__':
    # Teste de configuração
    try:
        DegustoneConfig.validate()
        print("[OK] Configuracoes validas")
        print(f"  CPF: {DegustoneConfig.CPF}")
        print(f"  Servidor: {DegustoneConfig.SERVIDOR_ID}")
        print(f"  Franquias: {DegustoneConfig.get_franquias_list()}")
        print(f"  Diretório de saída: {DegustoneConfig.OUTPUT_DIR}")
    except ValueError as e:
        print(f"[ERRO] Erro nas configuracoes: {e}")
