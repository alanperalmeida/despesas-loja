# 🚀 Instalação via Easypanel - Passo a Passo

## Informações da sua VPS
- IP: `46.62.214.201`
- Painel: Easypanel v2.26.0
- RAM: 4 GB
- Disco: 117 GB

---

## PARTE 1: Criar novo projeto

1. No Easypanel, clique em **"+ Novo"** (canto superior direito em "Projetos")
2. Nome do projeto: **despesas-degustone**
3. Clique em **Criar**

---

## PARTE 2: Adicionar PostgreSQL

1. Dentro do projeto **despesas-degustone**, clique em **"+ Adicionar Serviço"**
2. Escolha **"App Store"**
3. Procure por **"PostgreSQL"**
4. Clique em **Instalar**
5. Configure:
   - **Nome do serviço**: `postgres`
   - **Versão**: `16` (última)
   - **Database**: `despesas_db`
   - **Username**: `despesas`
   - **Password**: `SuaSenhaForte123` (anote essa senha!)
6. Em **"Persistência"**, marque para salvar em `/var/lib/postgresql/data`
7. Clique em **Deploy**

Aguarde o PostgreSQL subir (status verde).

---

## PARTE 3: Criar a tabela no PostgreSQL

### Via Easypanel (Console)
1. No serviço **postgres**, clique nos **3 pontinhos** → **Terminal**
2. No terminal, rode:
```bash
psql -U despesas -d despesas_db
```
3. Cole o SQL (do arquivo `create_table_despesas.sql`):
```sql
CREATE TABLE IF NOT EXISTS despesas_loja (
    id SERIAL PRIMARY KEY,
    franquia_id VARCHAR(20) NOT NULL,
    franquia_nome VARCHAR(200),
    data_extracao TIMESTAMP,
    data_despesa VARCHAR(20),
    grupo VARCHAR(200),
    descricao VARCHAR(500),
    fornecedor VARCHAR(500),
    valor VARCHAR(50),
    valor_numerico NUMERIC(15,2) DEFAULT 0,
    tabela_origem VARCHAR(10),
    arquivo_origem VARCHAR(200),
    data_carga TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uk_despesa_unica UNIQUE (franquia_id, data_despesa, descricao, fornecedor, valor)
);
```
4. Digite `\q` e Enter para sair

---

## PARTE 4: Adicionar Scraper API (Custom App)

1. Clique em **"+ Adicionar Serviço"** novamente
2. Escolha **"App"** (custom app)
3. Configure:

### General
- **Nome**: `scraper-api`
- **Source Type**: **GitHub**
- **Repository URL**: Precisamos criar um repo público OU usar upload manual

### OPÇÃO A: Upload manual via SSH (mais fácil)

**No seu Windows PowerShell**, envie os arquivos:
```powershell
scp -r C:\Users\user\Desktop\Despesasloja root@46.62.214.201:/tmp/despesas
```

Depois, **no terminal da VPS** (via Easypanel → hamburger menu → Terminal):
```bash
cd /tmp/despesas
# O Easypanel não tem acesso direto, então vamos criar a imagem primeiro
```

### OPÇÃO B: Criar imagem Docker manualmente (recomendado)

**No terminal da VPS** (Easypanel → menu → Terminal):

```bash
# 1. Criar pasta temporária
mkdir -p /tmp/despesas
cd /tmp/despesas

# 2. Você vai precisar copiar os arquivos via SFTP/SCP
# Use FileZilla conectando em:
#   - Host: sftp://46.62.214.201
#   - User: root
#   - Porta: 22
# Arraste a pasta Despesasloja para /tmp/despesas/
```

Depois de copiar os arquivos:
```bash
cd /tmp/despesas

# 3. Build da imagem
docker build -t scraper-api:latest .

# 4. Verificar
docker images | grep scraper
```

Volte ao Easypanel:

### Configuração do App
- **Source Type**: **Docker Image**
- **Image**: `scraper-api:latest`
- **Port**: `5679`

### Environment Variables
Adicione:
```
DEGUSTONE_CPF=14549094710
DEGUSTONE_SENHA=161097
HEADLESS=true
```

### Networking
- Marque **"Enable networking"**
- Port: `5679`

### Volumes
- Mount Path: `/app/relatorios`
- Host Path: deixe o Easypanel criar automaticamente

4. Clique em **Deploy**

---

## PARTE 5: Configurar n8n (usar o existente ou criar novo)

Vejo que você JÁ TEM o n8n rodando. Vamos usar esse!

1. Acesse seu n8n em: `http://46.62.214.201:PORTA_DO_N8N`
2. Vá em **Workflows → Import from File**
3. No seu Windows, selecione `C:\Users\user\Desktop\Despesasloja\n8n_workflow_despesas.json`

### Configurar PostgreSQL no n8n
1. No workflow, clique no nó **"4. Inserir no PostgreSQL"**
2. Credentials → Create New
3. Preencha:
   ```
   Host: postgres  (nome do serviço no Easypanel)
   Database: despesas_db
   User: despesas
   Password: SuaSenhaForte123
   Port: 5432
   SSL: Disabled
   ```

### Ajustar URL da API
Como os serviços estão na mesma rede Docker do Easypanel:
1. No nó **"1. Executar Scraper"**, mude a URL para:
   ```
   http://scraper-api:5679/scraper
   ```
2. No nó **"2. Buscar Dados"**, mude para:
   ```
   http://scraper-api:5679/data
   ```

---

## PARTE 6: Testar

1. No Easypanel, vá no serviço **scraper-api** → **Logs** (para acompanhar)
2. No n8n, clique em **Execute Workflow**
3. Aguarde 3-5 minutos
4. Verifique os logs no Easypanel para ver o scraper rodando

---

## ⚙️ Configurações adicionais

### Expor serviços publicamente (se necessário)
Se quiser acessar a API externamente:
1. No **scraper-api** → **Domains**
2. Adicione um domínio ou use o IP + porta
3. Easypanel vai criar automaticamente

### Monitoramento
- Vá em **"Monitorar"** no menu lateral
- Você verá CPU, RAM e logs de todos os serviços

---

## 🎯 Resumo do que foi criado

```
Projeto: despesas-degustone
├── postgres (PostgreSQL 16)
│   └── Database: despesas_db
│   └── Porta interna: 5432
│
├── scraper-api (Python + Playwright)
│   └── Porta: 5679
│   └── Volume: /app/relatorios
│
└── n8n (já existente no seu Easypanel)
    └── Conecta em postgres + scraper-api
    └── Workflow agendado para às 6h
```

---

## 🆘 Troubleshooting

**Se o scraper não buildar:**
- Veja os logs do build no Easypanel
- A primeira build pode demorar 10-15 minutos (baixa Chromium)

**Se n8n não conectar no PostgreSQL:**
- Use `postgres` como host (não `localhost` ou IP)
- Verifique se o serviço está rodando (status verde)

**Se precisar acessar o terminal de um serviço:**
- Clique nos 3 pontinhos do serviço → **Terminal**
