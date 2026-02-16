# 🐳 Guia de Deploy com Docker (VPS Linux)

Como você já tem o Docker instalado, esse é o método mais fácil e robusto.

## 1. Clonar o projeto na VPS
Acesse sua VPS via SSH e rode:

```bash
git clone https://github.com/alanperalmeida/despesas-loja.git
cd despesas-loja
```

## 2. Configurar Senhas (.env)
O arquivo de senhas não vem no git por segurança. Crie ele:

```bash
cp .env.example .env
nano .env
```
(Cole suas credenciais do Degustone e do Banco de Dados no editor e salve com `Ctrl+O`, `Enter`, `Ctrl+X`)

## 3. Subir os serviços
Esse comando vai baixar as imagens, criar o banco de dados e deixar tudo rodando em segundo plano:

```bash
docker compose up -d --build
```

**O que isso sobe?**
- 🐘 **PostgreSQL**: Banco de dados (porta 5432)
- 🐍 **Scraper API**: API Python para rodar o scraping (porta 5679)
- 🤖 **n8n**: Automação de workflow (porta 5678)

## 4. Usar o Scraper
Você tem duas opções:

### Opção A: Via Linha de Comando (Manual)
Para rodar o scraper "dentro" do container Docker:

```bash
# Rodar para todas as franquias
docker compose exec scraper-api python degustone_scraper.py --headless

# Rodar para uma franquia especifica
docker compose exec scraper-api python degustone_scraper.py --franquia 1866 --headless
```

### Opção B: Via n8n (Automático)
Acesse `http://SEU_IP_DA_VPS:5678` para configurar o workflow visual.

## 🔒 Dica de Ouro: Atualizar Código
Se você mudou algo no código no seu computador e quer atualizar na VPS:

```bash
git pull origin main
docker compose up -d --build
```
(O `--build` é importante para atualizar o código Python dentro do container)
