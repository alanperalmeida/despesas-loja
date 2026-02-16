# Automação de Extração de Relatórios Degustone

Sistema completo de web scraping para extração automatizada de relatórios de despesas do sistema Degustone.

## 📋 Visão Geral

Este projeto contém scripts Python e documentação para automatizar a extração de relatórios de despesas do site Degustone, com integração para n8n.

## 🚀 Quick Start

### 1. Instalar Dependências

```bash
cd C:\Users\user\Desktop\Despesasloja
pip install -r requirements.txt
playwright install chromium
```

### 2. Configurar Credenciais

```bash
# Copiar template
cp .env.example .env

# Editar .env com suas credenciais
# (já pré-configurado com credenciais fornecidas)
```

### 3. Executar

```bash
# Extrair relatórios de todas as franquias
python degustone_scraper.py --headless

# Extrair relatório de franquia específica
python degustone_scraper.py --franquia 1866 --headless

# Executar com navegador visível (debug)
python degustone_scraper.py --visible
```

## 📁 Estrutura do Projeto

```
Despesasloja/
├── config.py                    # Configurações centralizadas
├── degustone_scraper.py         # Script principal (Playwright)
├── api_client.py                # Cliente HTTP alternativo
├── requirements.txt             # Dependências Python
├── .env.example                 # Template de configuração
├── .env                         # Configurações (criar você mesmo)
├── GUIA_N8N.md                  # Guia de integração com n8n
├── FLUXO_AUTENTICACAO.md        # Documentação técnica
├── README.md                    # Este arquivo
└── relatorios/                  # Diretório de saída (criado automaticamente)
    ├── relatorio_franquia_1866_*.json
    ├── relatorio_franquia_1866_*.html
    └── relatorio_franquia_1866_*.png
```

## 🔧 Componentes

### degustone_scraper.py
Script principal usando Playwright para automação completa do navegador.

**Características:**
- ✅ Login automático
- ✅ Seleção de servidor e franquia
- ✅ Extração de dados estruturados
- ✅ Screenshots do relatório
- ✅ Seletores CSS flexíveis
- ✅ Tratamento robusto de erros
- ✅ Suporte a múltiplas franquias

**Uso:**
```bash
python degustone_scraper.py --franquia 1866 --headless
```

### api_client.py
Cliente alternativo usando requisições HTTP diretas (sem navegador).

**Características:**
- ✅ Mais rápido que navegador
- ✅ Menor consumo de recursos
- ✅ Funciona em ambientes sem GUI
- ⚠️ Pode não funcionar se site usar muito JavaScript

**Uso:**
```bash
python api_client.py --franquia 1866
```

### config.py
Módulo de configuração centralizada.

**Recursos:**
- Carrega variáveis de ambiente
- Validação de configurações
- Gerenciamento de diretórios

## ⚙️ Configuração

### Variáveis de Ambiente (.env)

```env
# Credenciais
DEGUSTONE_CPF=14549094710
DEGUSTONE_SENHA=161097

# Servidor e Franquias
SERVIDOR_ID=1
FRANQUIAS=1866,2610,3127

# URLs (não precisa alterar)
BASE_URL=https://degustone.com.br
LOGIN_URL=https://degustone.com.br/login
ACESSO_URL=https://degustone.com.br/acesso
RELATORIO_URL=https://degustone.com.br/relatorio/despesas-loja

# Opções de Scraping
HEADLESS=true
TIMEOUT=30000
RETRY_ATTEMPTS=3

# Saída
OUTPUT_DIR=./relatorios
```

## 🤖 Integração com n8n

Consulte o [GUIA_N8N.md](GUIA_N8N.md) para instruções detalhadas.

### Resumo Rápido:

1. **Adicionar Schedule Trigger** (agendamento)
2. **Adicionar Execute Command Node:**
   ```
   python C:\Users\user\Desktop\Despesasloja\degustone_scraper.py --headless
   ```
3. **Processar resultados** (ler JSONs gerados)

## 📊 Formato de Saída

### JSON
```json
{
  "franquia_id": "1866",
  "timestamp": "2026-02-13T17:45:00",
  "tables_count": 1,
  "tables": [
    {
      "table_index": 0,
      "rows": [
        ["Data", "Categoria", "Valor"],
        ["2026-02-13", "Aluguel", "R$ 5.000,00"]
      ]
    }
  ]
}
```

### Arquivos Gerados
- `relatorio_franquia_1866_20260213_174500.json` - Dados estruturados
- `relatorio_franquia_1866_20260213_174500.html` - HTML completo
- `relatorio_franquia_1866_20260213_174500.png` - Screenshot

## 🐛 Troubleshooting

### Erro: "Playwright not installed"
```bash
playwright install chromium
```

### Erro: "Campo de login não encontrado"
Execute com `--visible` para ver o que está acontecendo:
```bash
python degustone_scraper.py --visible
```

### Erro: "Timeout"
Aumente o timeout no `.env`:
```env
TIMEOUT=60000
```

### Script não funciona no n8n
1. Verifique se Python está no PATH
2. Use caminho absoluto completo
3. Teste manualmente primeiro

## 📚 Documentação Adicional

- [GUIA_N8N.md](GUIA_N8N.md) - Integração completa com n8n
- [FLUXO_AUTENTICACAO.md](FLUXO_AUTENTICACAO.md) - Detalhes técnicos de autenticação

## 🔒 Segurança

- ⚠️ Nunca commite o arquivo `.env` (contém credenciais)
- ✅ Use `.env.example` como template
- ✅ Mantenha as credenciais seguras
- ✅ Use variáveis de ambiente em produção

## 📝 Logs

Os scripts geram logs detalhados:

```
2026-02-13 17:45:00 - INFO - Iniciando navegador...
2026-02-13 17:45:02 - INFO - Navegador iniciado com sucesso
2026-02-13 17:45:02 - INFO - Acessando página de login: https://degustone.com.br/login
2026-02-13 17:45:04 - INFO - CPF preenchido usando seletor: input[name="cpf"]
2026-02-13 17:45:04 - INFO - Senha preenchida usando seletor: input[type="password"]
2026-02-13 17:45:05 - INFO - Login realizado com sucesso
...
```

## 🎯 Casos de Uso

### 1. Extração Agendada Diária
Usar n8n com Schedule Trigger às 8h para extrair relatórios automaticamente.

### 2. Extração sob Demanda
Executar script manualmente quando necessário.

### 3. Integração com BI
Processar JSONs gerados e enviar para ferramenta de BI.

### 4. Alertas Automáticos
Analisar despesas e enviar alertas quando ultrapassar limites.

## 🤝 Suporte

Em caso de problemas:
1. Verifique os logs
2. Execute com `--visible` para debug
3. Consulte a documentação técnica
4. Verifique se credenciais estão corretas


## 💻 Guia de Desenvolvimento (Git)

### Em outro computador (Novo Setup)
1. **Clonar o repositório:**
   ```bash
   git clone https://github.com/alanperalmeida/despesas-loja.git
   cd despesas-loja
   ```
2. **Configurar Ambiente:**
   ```bash
   # Criar ambiente virtual
   python -m venv venv
   .\venv\Scripts\activate
   
   # Instalar dependências
   pip install -r requirements.txt
   playwright install chromium
   ```
3. **Criar .env:**
   - Copie `.env.example` para `.env`
   - Preencha suas credenciais

### Fluxo de Trabalho (Dia a Dia)
1. **Atualizar código (antes de começar):**
   ```bash
   git pull origin main
   ```
2. **Fazer alterações** no código via VS Code ou editor.
3. **Enviar alterações:**
   ```bash
   git add .
   git commit -m "Descrição do que foi feito"
   git push origin main
   ```

## 📄 Licença


Este projeto é fornecido como está, para uso pessoal.
