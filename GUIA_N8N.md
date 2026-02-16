# Guia de Integração com n8n

Este guia explica como configurar a automação de extração de relatórios Degustone no n8n.

## Opções de Integração

Existem 2 principais formas de integrar com n8n:

### 1. Usando Execute Command Node (Recomendado)
### 2. Usando HTTP Request Nodes (Avançado)

---

## Opção 1: Execute Command Node

Esta é a forma mais simples e confiável.

### Pré-requisitos

1. **Instalar Python** no servidor do n8n
2. **Instalar dependências:**
   ```bash
   cd C:\Users\user\Desktop\Despesasloja
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Configurar arquivo .env:**
   ```bash
   cp .env.example .env
   # Editar .env com suas credenciais
   ```

### Configuração do Workflow n8n

#### Node 1: Schedule Trigger
- **Tipo:** Schedule Trigger
- **Configuração:** 
  - Modo: Every Day
  - Hora: 08:00 (ou horário desejado)
  - Timezone: America/Sao_Paulo

#### Node 2: Execute Command
- **Tipo:** Execute Command
- **Configuração:**
  ```
  Command: python
  Arguments: C:\Users\user\Desktop\Despesasloja\degustone_scraper.py --headless
  ```
- **Opções Avançadas:**
  - Execute Once: Yes
  - Timeout: 300000 (5 minutos)

#### Node 3: Read Binary Files (Opcional)
- **Tipo:** Read Binary Files
- **File Path:** `C:\Users\user\Desktop\Despesasloja\relatorios\*.json`
- **Serve para:** Ler os arquivos JSON gerados

#### Node 4: Process Data (Opcional)
- **Tipo:** Code ou Function
- **Objetivo:** Processar os dados extraídos
- **Exemplo:**
  ```javascript
  const reports = items[0].json;
  
  // Processar dados conforme necessário
  return reports.map(report => ({
    json: {
      franquia: report.franquia_id,
      timestamp: report.timestamp,
      tables: report.tables
    }
  }));
  ```

#### Node 5: Send Email / Webhook / Database (Opcional)
- Enviar resultados por email
- Enviar para sistema externo via webhook
- Salvar em banco de dados

### Workflow Completo (JSON)

```json
{
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "hours",
              "hoursInterval": 24
            }
          ]
        }
      },
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "position": [250, 300],
      "typeVersion": 1
    },
    {
      "parameters": {
        "command": "python C:\\Users\\user\\Desktop\\Despesasloja\\degustone_scraper.py --headless"
      },
      "name": "Execute Scraper",
      "type": "n8n-nodes-base.executeCommand",
      "position": [450, 300],
      "typeVersion": 1
    },
    {
      "parameters": {
        "filePath": "C:\\Users\\user\\Desktop\\Despesasloja\\relatorios\\*.json"
      },
      "name": "Read Results",
      "type": "n8n-nodes-base.readBinaryFiles",
      "position": [650, 300],
      "typeVersion": 1
    }
  ],
  "connections": {
    "Schedule Trigger": {
      "main": [[{"node": "Execute Scraper", "type": "main", "index": 0}]]
    },
    "Execute Scraper": {
      "main": [[{"node": "Read Results", "type": "main", "index": 0}]]
    }
  }
}
```

---

## Opção 2: HTTP Request Nodes (Avançado)

Esta opção requer mais configuração mas não depende de executar scripts Python.

### Workflow com HTTP Requests

#### Node 1: Schedule Trigger
(mesmo da Opção 1)

#### Node 2: HTTP Request - Login
- **Tipo:** HTTP Request
- **Método:** POST
- **URL:** `https://degustone.com.br/login`
- **Authentication:** None
- **Headers:**
  ```
  Content-Type: application/x-www-form-urlencoded
  User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
  ```
- **Body:**
  ```
  cpf=14549094710
  password=161097
  ```
- **Options:**
  - Follow Redirect: Yes
  - Keep Cookies: Yes

#### Node 3: HTTP Request - Selecionar Franquia
- **Tipo:** HTTP Request
- **Método:** POST
- **URL:** `https://degustone.com.br/acesso`
- **Options:**
  - Use Cookies from Previous Node: Yes
- **Body:**
  ```
  servidor=1
  franquia=1866
  ```

#### Node 4: HTTP Request - Obter Relatório
- **Tipo:** HTTP Request
- **Método:** GET
- **URL:** `https://degustone.com.br/relatorio/despesas-loja`
- **Options:**
  - Use Cookies from Previous Node: Yes

#### Node 5: HTML Extract
- **Tipo:** HTML Extract
- **Usar para extrair dados da resposta HTML**
- **CSS Selectors:**
  - Para tabelas: `table`
  - Para linhas: `tr`
  - Para células: `td`

---

## Executando Franquias Específicas

### Para uma franquia específica:
```bash
python degustone_scraper.py --franquia 1866 --headless
```

### Para todas as franquias:
```bash
python degustone_scraper.py --headless
```

### Loop no n8n para múltiplas franquias:

Adicione um node **Split In Batches** antes do Execute Command:

```javascript
// Node: Function - Prepare Franchises
return [
  { json: { franquia: '1866' } },
  { json: { franquia: '2610' } },
  { json: { franquia: '3127' } }
];
```

Depois usar **Execute Command** com:
```
python C:\Users\user\Desktop\Despesasloja\degustone_scraper.py --franquia {{$json.franquia}} --headless
```

---

## Tratamento de Erros

### No n8n:

1. **Adicionar Error Trigger:**
   - Detecta quando workflow falha
   - Envia notificação

2. **Retry Logic:**
   - Em cada HTTP Request node
   - Configurar "Retry On Fail": 3 vezes
   - "Wait Between Tries": 5000ms

3. **Node de Notificação:**
   - Enviar email em caso de erro
   - Enviar para Slack/Discord/Telegram

---

## Agendamento

### Exemplos de agendamento:

**Diário às 8h:**
```
Cron: 0 8 * * *
```

**A cada 6 horas:**
```
Cron: 0 */6 * * *
```

**Segunda a Sexta às 9h:**
```
Cron: 0 9 * * 1-5
```

---

## Monitoramento

### Logs

Os scripts Python geram logs detalhados:
- Sucesso/falha de login
- Franquias processadas
- Arquivos salvos
- Erros encontrados

### Arquivos de Saída

Todos os relatórios são salvos em:
```
C:\Users\user\Desktop\Despesasloja\relatorios\
```

Com nomenclatura:
- `relatorio_franquia_1866_20260213_174500.json`
- `relatorio_franquia_1866_20260213_174500.html`
- `relatorio_franquia_1866_20260213_174500.png` (screenshot)

---

## Troubleshooting

### Erro: "Playwright not installed"
```bash
playwright install chromium
```

### Erro: "Campo de login não encontrado"
- Execute com `--visible` para ver o navegador
- Verifique se os seletores CSS precisam ser ajustados no código

### Erro: "Timeout"
- Aumente o timeout no `.env`: `TIMEOUT=60000`
- Verifique conexão com internet

### Script não executa no n8n
- Verifique permissões do arquivo
- Use caminho absoluto completo
- Teste o comando manualmente primeiro

---

## Próximos Passos

1. Testar manualmente o script
2. Importar workflow no n8n
3. Configurar agendamento
4. Configurar notificações de erro
5. Integrar com sistema de destino (email, database, etc.)
