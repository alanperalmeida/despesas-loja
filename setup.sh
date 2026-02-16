#!/bin/bash

echo "=========================================="
echo "Configurando Ambiente Despesasloja (Linux)"
echo "=========================================="

# 1. Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python3 nao encontrado! Instale com: sudo apt install python3"
    exit 1
fi

echo ""
echo "2. Criando ambiente virtual (venv)..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Venv criado."
else
    echo "Venv ja existe."
fi

echo ""
echo "3. Instalando dependencias..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "4. Instalando navegadores do Playwright..."
playwright install chromium
# Instalar dependencias de sistema do Playwright (requer sudo)
echo "Tentando instalar dependencias do sistema para Playwright (pode pedir senha sudo)..."
sudo playwright install-deps chromium

echo ""
echo "5. Configurando credenciais (.env)..."
if [ ! -f ".env" ]; then
    echo "Criando .env a partir do exemplo..."
    cp .env.example .env
    echo ""
    echo "[ATENCAO] O arquivo .env foi criado."
    echo "[ATENCAO] Voce PRECISA editar o arquivo .env e colocar suas senhas!"
else
    echo "Arquivo .env ja existe."
fi

echo ""
echo "=========================================="
echo "SETUP CONCLUIDO COM SUCESSO!"
echo "=========================================="
echo "Para rodar o codigo:"
echo "1. Digite: source venv/bin/activate"
echo "2. Digite: python degustone_scraper.py"
echo "=========================================="
