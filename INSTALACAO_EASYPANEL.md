# 🚀 Instalação via Easypanel + GitHub

Como o código já está no GitHub, o processo é **MUITO SIMPLES**. O Easypanel vai baixar o código, criar a imagem Docker e rodar tudo automaticamente.

---

## Passo 1: Preparação

1. **Acesse seus projetos** no Easypanel.
2. Como você já tem o projeto **"n8n"** rodando, vamos adicionar os serviços nele para facilitar a comunicação.
3. Abra o projeto **"n8n"** (ou "meus-apps" se preferir, mas certifique-se que o n8n consegue acessar).

---

## Passo 2: Criar Banco de Dados (PostgreSQL)

*Se você já tem um Postgres configurado e quer usar o mesmo, pule esta etapa e use as credenciais existentes.*

1. Dentro do projeto, clique em **"+ Service"** -> **App Store**.
2. Procure por **PostgreSQL**.
3. Configure:
   - **Name**: `postgres` (Importante ser esse nome)
   - **Database**: `despesas_db`
   - **User**: `despesas`
   - **Password**: `SuaSenhaForteAqui`
4. Clique em **Create**.

---

## Passo 3: Criar API do Scraper (A Mágica!)

1. Clique em **"+ Service"** -> **App**.
2. Dê o nome de `scraper-api`.
3. Vá na aba **General**:
   - **Source**: `Git` (ou GitHub)
   - **Repository**: `https://github.com/alanperalmeida/despesas-loja`
   - **Branch**: `main`
   - **Build Method**: `Dockerfile` (padrão)
   
4. Vá na aba **Environment**:
   - Adicione as variáveis do seu arquivo `.env` MANUALMENTE aqui:
     - `DEGUSTONE_CPF` = `seu_cpf`
     - `DEGUSTONE_SENHA` = `sua_senha`
     - `POSTGRES_HOST` = `postgres` (se estiver no mesmo projeto)
     - `POSTGRES_DB` = `despesas_db`
     - `POSTGRES_USER` = `despesas`
     - `POSTGRES_PASSWORD` = `SuaSenhaForteAqui`
     - `HEADLESS` = `true`

5. Vá na aba **Networking**:
   - **HTTP Port**: `5679` (Isso é muito importante!)
   - **Public**: Opcional (se quiser acessar de fora). Se for só pro n8n, não precisa.

6. Clique em **Deploy**.

O Easypanel vai baixar o código do GitHub, instalar tudo (pode demorar uns 3-5 min na primeira vez) e subir o serviço.

---

## Passo 4: Conectar com n8n

No seu n8n (que já está rodando), configure os nodes HTTP:

1. **URL do Scraper**: 
   - Use `http://scraper-api:5679` (se estiverem no mesmo projeto)
   - Ou use o IP interno/nome do serviço.

2. **Testar**:
   - Mande rodar o workflow. Se o scraper-api estiver verde (Running), vai funcionar!

---

## 🔄 Como atualizar depois?

Se você mexer no código no seu PC:
1. `git push origin main`
2. No Easypanel, vá no serviço `scraper-api` e clique em **Deploy**.
Ele baixa a nova versão e atualiza sozinho! 🚀
