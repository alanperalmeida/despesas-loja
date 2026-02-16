# 🚀 Instalação Recomendada (Mesmo Projeto do n8n)

Para **reutilizar seu Banco de Dados** existente e simplificar a conexão, a melhor opção é instalar tudo no **mesmo projeto**.

**⚠️ Vai dar conflito?**
**NÃO.** O Easypanel usa Docker. Cada serviço é isolado em seu próprio container. O `scraper-api` não consegue tocar nos arquivos do `n8n` e vice-versa. É seguro.

---

## Passo 1: Pegar Credencias do Banco Existente

1. Abra seu projeto **"n8n"** (ou onde está seu banco).
2. Clique no serviço do Banco de Dados (ex: `postgres` ou `n8nchat-db`).
3. Vá na aba **Environment** ou desça até ver as credenciais.
4. Anote:
   - **Host** (Nome do serviço): geralmente `postgres`
   - **Database**: nome do banco (confirme se é `despesas_db` ou se quer usar o existente)
   - **User**: usuário do banco
   - **Password**: senha do banco

---

## Passo 2: Adicionar API do Scraper

1. No mesmo projeto, clique em **"+ Service"** -> **App**.
2. Nome: `scraper-api`.
3. **General**:
   - **Source**: `Git`
   - **Repository**: `https://github.com/alanperalmeida/despesas-loja`
   - **Branch**: `main`
   - **Build Method**: `Dockerfile`

4. **Environment** (Aqui está o segredo):
   - Use as credenciais que você anotou do SEU banco:
     - `POSTGRES_HOST` = `postgres` (ou o nome do serviço do seu banco)
     - `POSTGRES_DB` = `nome_do_seu_banco`
     - `POSTGRES_USER` = `seu_usuario`
     - `POSTGRES_PASSWORD` = `sua_senha`
     - `DEGUSTONE_CPF` = `...`
     - `DEGUSTONE_SENHA` = `...`
     - `HEADLESS` = `true`

5. **Networking**:
   - **HTTP Port**: `5679`
   - Não precisa de domínio público se for usar só no n8n.

6. Clique em **Deploy**.

---

## Passo 3: Verificar Tabela

O scraper vai tentar salvar na tabela `despesas_loja`.
- Se você já criou essa tabela no seu banco: **Ótimo!** Ele vai usar.
- Se não, rode o script SQL `create_table_despesas.sql` no seu banco via terminal do Easypanel.

---

## Passo 4: No n8n

Como estão no mesmo projeto, a comunicação é interna:
- URL Scraper: `http://scraper-api:5679`
- Credenciais Postgres do n8n: Use as mesmas do Passo 1 (`postgres`, usuário, senha...).

Pronto! Tudo integrado, sem duplicar banco e sem conflitos. 🚀
