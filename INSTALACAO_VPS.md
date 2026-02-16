# 📦 Instalação na VPS - Passo a Passo Completo

## ✅ Pré-requisitos
- VPS Linux (Ubuntu 22.04 ou Debian 12)
- Acesso SSH (usuário root ou com sudo)
- IP da VPS
- Pelo menos 2GB de RAM

---

## 🔧 PARTE 1: Preparar a VPS

### 1.1 Conectar na VPS via SSH
No seu Windows, abra o PowerShell ou use PuTTY:
```bash
ssh root@SEU_IP_DA_VPS
# Ou se tiver usuário não-root:
ssh usuario@SEU_IP_DA_VPS
```

### 1.2 Atualizar o sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.3 Instalar Docker
```bash
# Instalar Docker com o script oficial
curl -fsSL https://get.docker.com | sh

# Adicionar seu usuário ao grupo docker (se não for root)
sudo usermod -aG docker $USER

# IMPORTANTE: Sair e entrar novamente no SSH para aplicar
exit
# Conecte novamente
ssh usuario@SEU_IP_DA_VPS
```

### 1.4 Verificar instalação
```bash
docker --version
docker compose version
```
Deve mostrar versões 20+ do Docker.

---

## 📤 PARTE 2: Enviar arquivos da pasta Despesasloja

### Opção A: Via SCP (mais rápido)
No seu **Windows PowerShell**:
```powershell
# Substitua 'usuario' e 'SEU_IP_DA_VPS' pelos valores reais
scp -r C:\Users\user\Desktop\Despesasloja usuario@SEU_IP_DA_VPS:/home/usuario/despesas
```

### Opção B: Via FileZilla/WinSCP (visual)
1. Baixe e instale [FileZilla](https://filezilla-project.org/) ou [WinSCP](https://winscp.net/)
2. Conecte usando:
   - Host: `SEU_IP_DA_VPS`
   - Usuário: `usuario` (ou `root`)
   - Senha: sua senha SSH
   - Porta: `22`
3. Arraste a pasta `C:\Users\user\Desktop\Despesasloja` para `/home/usuario/despesas`

---

## ⚙️ PARTE 3: Configurar na VPS

### 3.1 Entrar na pasta
```bash
cd ~/despesas
ls -la  # Ver todos os arquivos
```

Você deve ver:
- `Dockerfile`
- `docker-compose.yml`
- `degustone_scraper.py`
- `api_server.py`
- `config.py`
- `.env.example`
- etc.

### 3.2 Criar o arquivo .env com suas credenciais
```bash
cp .env.example .env
nano .env
```

Edite o arquivo (use as setas, escreva, Ctrl+O para salvar, Ctrl+X para sair):
```bash
# Credenciais Degustone
DEGUSTONE_CPF=14549094710
DEGUSTONE_SENHA=161097

# PostgreSQL (mude a senha!)
POSTGRES_USER=despesas
POSTGRES_PASSWORD=SenhaSuperForte123
POSTGRES_DB=despesas_db

# n8n (mude usuário e senha!)
N8N_USER=admin
N8N_PASSWORD=MinhaSenh@N8n123
N8N_HOST=SEU_IP_DA_VPS
```

> ⚠️ **IMPORTANTE**: Troque `POSTGRES_PASSWORD` e `N8N_PASSWORD` por senhas fortes!

---

## 🚀 PARTE 4: Subir tudo com Docker

### 4.1 Build e executar todos os containers
```bash
docker compose up -d --build
```

Isso vai:
1. Baixar imagens do PostgreSQL e n8n (~500MB)
2. Buildar o container do scraper Python (~1GB - pode demorar 5-10 min na primeira vez)
3. Criar banco de dados e tabela automaticamente
4. Subir 3 containers: `postgres`, `scraper-api`, `n8n`

### 4.2 Verificar se está tudo rodando
```bash
docker compose ps
```

Deve mostrar 3 containers com status **Up**:
```
NAME                 IMAGE              STATUS
despesas-postgres    postgres:16        Up
despesas-scraper     despesas-scraper   Up
despesas-n8n         n8nio/n8n          Up
```

### 4.3 Ver os logs (para debug)
```bash
# Ver logs de todos
docker compose logs

# Ver logs em tempo real
docker compose logs -f

# Ver logs apenas do scraper
docker compose logs -f scraper-api
```

---

## 🌐 PARTE 5: Acessar o n8n e configurar

### 5.1 Abrir o n8n no navegador
```
http://SEU_IP_DA_VPS:5678
```

Login com:
- Usuário: `admin` (ou o que definiu no .env)
- Senha: `MinhaSenh@N8n123` (ou o que definiu no .env)

### 5.2 Importar o workflow
1. No n8n, clique no menu superior: **Workflows → Import from File**
2. **No seu Windows**, vá em `C:\Users\user\Desktop\Despesasloja\n8n_workflow_despesas.json`
3. Arraste para o n8n ou clique em "Upload"

O workflow com 6 nós vai aparecer!

### 5.3 Configurar a conexão com PostgreSQL
1. Clique no nó **"4. Inserir no PostgreSQL"**
2. Clique em **"Credentials for Postgres"**
3. Clique em **"Create New Credential"**
4. Preencha:
   ```
   Name: PostgreSQL Despesas
   Host: postgres
   Database: despesas_db
   User: despesas
   Password: SenhaSuperForte123  (a que você definiu no .env)
   Port: 5432
   SSL: Disabled
   ```
5. Clique em **"Save"**

---

## ✅ PARTE 6: Testar

### 6.1 Testar a API manualmente
Na VPS:
```bash
curl http://localhost:5679/health
```
Deve retornar:
```json
{"status": "ok", "timestamp": "2026-02-14T..."}
```

### 6.2 Testar o scraper manualmente (opcional)
```bash
docker exec -it despesas-scraper python api_server.py &
# Ou rodar o scraper direto:
docker exec -it despesas-scraper python degustone_scraper.py --headless
```

### 6.3 Testar o workflow no n8n
1. No n8n, clique no botão **"Execute Workflow"** (canto superior direito)
2. Aguarde uns 3-5 minutos
3. Se tudo estiver OK, você verá o resumo no nó "5. Resumo"

---

## 🛠️ Comandos úteis pós-instalação

```bash
# Ver status dos containers
docker compose ps

# Ver logs
docker compose logs -f

# Reiniciar tudo
docker compose restart

# Parar tudo
docker compose down

# Parar e deletar volumes (CUIDADO: perde dados!)
docker compose down -v

# Atualizar código do scraper
docker compose up -d --build scraper-api

# Entrar no container do scraper (debug)
docker exec -it despesas-scraper bash

# Ver banco de dados PostgreSQL
docker exec -it despesas-postgres psql -U despesas -d despesas_db
# Dentro do psql:
\dt                    # Listar tabelas
SELECT * FROM despesas_loja LIMIT 10;
\q                     # Sair
```

---

## 🔒 PARTE 7: Segurança (IMPORTANTE!)

### 7.1 Configurar Firewall
```bash
# Permitir apenas portas necessárias
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 5678/tcp    # n8n
sudo ufw enable
```

### 7.2 (Opcional) Configurar HTTPS com domínio
Se você tiver um domínio (ex: `despesas.seudominio.com`):
1. Aponte o domínio para o IP da VPS (DNS tipo A)
2. Use Nginx Proxy Manager ou Caddy para HTTPS automático
3. Altere `N8N_HOST` no `.env` para `despesas.seudominio.com`

---

## 📊 PARTE 8: Agendar execução diária

O workflow **já está configurado** para rodar todo dia às **6h da manhã** automaticamente.

Para alterar o horário:
1. No n8n, clique no nó **"Trigger Diário 6h"**
2. Altere o campo **"Hour"** e **"Minute"**
3. Salve o workflow

---

## ❓ Solução de problemas

### Container não sobe
```bash
docker compose logs scraper-api
# Ver erro específico
```

### n8n não conecta no PostgreSQL
- Verifique se a senha no `.env` está correta
- Verifique se a credential no n8n usa `postgres` como host (não `localhost`)

### Scraper dá timeout
- Primeira execução demora mais (até 10 min)
- Veja logs: `docker compose logs -f scraper-api`

### Porta 5678 não abre
```bash
# Verificar se está ouvindo
netstat -tlnp | grep 5678

# Verificar firewall
sudo ufw status
```

---

## 🎉 Pronto!

O sistema agora está rodando 24/7 na VPS:
- ✅ n8n rodando em `http://SEU_IP:5678`
- ✅ Scraper pronto para ser chamado
- ✅ PostgreSQL armazenando dados
- ✅ Execução automática diária às 6h
