@echo off
echo ==========================================
echo Configurando Ambiente Despesasloja
echo ==========================================

echo 1. Verificando Python...
python --version
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado! Instale o Python e marque "Add to PATH".
    pause
    exit /b
)

echo.
echo 2. Criando ambiente virtual (venv)...
if not exist venv (
    python -m venv venv
    echo Venv criado.
) else (
    echo Venv ja existe.
)

echo.
echo 3. Ativando ambiente e instalando dependencias...
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo 4. Instalando navegadores do Playwright...
playwright install chromium

echo.
echo 5. Configurando credenciais (.env)...
if not exist .env (
    echo Criando .env a partir do exemplo...
    copy .env.example .env
    echo.
    echo [ATENCAO] O arquivo .env foi criado.
    echo [ATENCAO] Voce PRECISA abrir o arquivo .env e colocar suas senhas!
) else (
    echo Arquivo .env ja existe.
)

echo.
echo ==========================================
echo SETUP CONCLUIDO COM SUCESSO!
echo ==========================================
echo Para rodar o codigo:
echo 1. Digite: venv\Scripts\activate
echo 2. Digite: python degustone_scraper.py
echo ==========================================
pause
