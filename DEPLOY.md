# 🚀 Deploy na VPS Linux

## Pré-requisitos
- VPS com Ubuntu 22.04+ (mínimo 2GB RAM)
- Docker e Docker Compose instalados

## 1. Instalar Docker (se não tiver)
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Saia e entre novamente no SSH
```

## 2. Enviar os arquivos para a VPS
No seu Windows, abra o terminal e rode:
```bash
scp -r C:\Users\user\Desktop\Despesasloja usuario@IP_DA_VPS:~/despesas
```
Ou use o FileZilla/WinSCP para copiar a pasta inteira.

## 3. Configurar o .env
```bash
cd ~/despesas
cp .env.example .env
nano .env
```
Preencha as credenciais:
```
DEGUSTONE_CPF=14549094710
DEGUSTONE_SENHA=161097
POSTGRES_USER=despesas
POSTGRES_PASSWORD=SUA_SENHA_FORTE
POSTGRES_DB=despesas_db
N8N_USER=admin
N8N_PASSWORD=SUA_SENHA_N8N
N8N_HOST=IP_DA_VPS
```

## 4. Subir tudo
```bash
docker compose up -d --build
```
Isso vai:
- Criar o banco PostgreSQL (com a tabela `despesas_loja` automaticamente)
- Buildar e rodar o scraper API na porta 5679
- Rodar o n8n na porta 5678

## 5. Acessar o n8n
Abra no navegador: `http://IP_DA_VPS:5678`

Login:
- Usuário: `admin` (ou o que definiu no .env)
- Senha: `admin123` (ou o que definiu no .env)

## 6. Importar o workflow
1. No n8n, vá em **Workflows → Import from File**
2. Selecione `n8n_workflow_despesas.json`
3. Configure a credential do PostgreSQL:
   - Host: `postgres`
   - Port: `5432`
   - Database: `despesas_db`
   - User: `despesas`
   - Password: (a que definiu no .env)

## 7. Testar
Clique em **Execute Workflow** para rodar manualmente.

## Comandos úteis
```bash
# Ver logs
docker compose logs -f

# Ver logs do scraper
docker compose logs -f scraper-api

# Reiniciar tudo
docker compose restart

# Parar tudo
docker compose down

# Atualizar código
docker compose up -d --build scraper-api
```
