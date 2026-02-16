# 🚀 Instalação via Easypanel + GitHub (Projeto Separado)

Para manter a organização e evitar conflitos com seu n8n atual, vamos criar um projeto novo.

---

## Passo 1: Criar Novo Projeto

1. No Easypanel, clique em **"+ Novo"**.
2. Nome: `despesas-degustone`.
3. Clique em **Criar**.

---

## Passo 2: Criar Banco de Dados (PostgreSQL)

1. Dentro do projeto `despesas-degustone`, clique em **"+ Service"** -> **App Store**.
2. Procure por **PostgreSQL**.
3. Configure:
   - **Name**: `postgres`
   - **Database**: `despesas_db`
   - **User**: `despesas`
   - **Password**: `SuaSenhaForteAqui`
4. Clique em **Create**.

---

## Passo 3: Criar API do Scraper

1. Clique em **"+ Service"** -> **App**.
2. Nome: `scraper-api`.
3. **General**:
   - **Source**: `Git` (ou GitHub)
   - **Repository**: `https://github.com/alanperalmeida/despesas-loja`
   - **Branch**: `main`
   - **Build Method**: `Dockerfile`

4. **Environment**:
   - Adicione suas variáveis do `.env` aqui:
     - `DEGUSTONE_CPF` = `...`
     - `DEGUSTONE_SENHA` = `...`
     - `POSTGRES_HOST` = `postgres` (conexão interna no mesmo projeto)
     - `POSTGRES_DB` = `despesas_db`
     - `POSTGRES_USER` = `despesas`
     - `POSTGRES_PASSWORD` = `SuaSenhaForteAqui`
     - `HEADLESS` = `true`

5. **Networking (Importante para comunicar com n8n)**:
   - **HTTP Port**: `5679`
   - **Domains**: Clique em "+ Domain". 
     - O Easypanel vai gerar um domínio automático (ex: `scraper-api.seu-easypanel.com`).
     - **Anote esse domínio!** Seu n8n vai usar ele para acessar a API.

6. Clique em **Deploy**.

---

## Passo 4: Conectar n8n (que está em outro projeto)

No seu n8n, nos nodes HTTP:

1. **URL do Scraper**: 
   - Use o domínio público que você criou no passo anterior:
   - Ex: `https://scraper-api.seu-easypanel.com/scraper`
   
   ⚠️ **Não use** `http://scraper-api:5679` (isso só funciona se estivessem no mesmo projeto).
   ✅ **Use** `https://seudominio.com/scraper`

2. **Segurança (Recomendado)**:
   - Como a API ficará pública, considere adicionar uma senha simples no código ou usar o "Basic Auth" do Easypanel na aba "Security" do serviço.

---

## 🔄 Como atualizar?

Igual antes: `git push` no seu PC -> botão **Deploy** no Easypanel.
