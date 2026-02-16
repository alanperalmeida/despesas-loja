"""
Diagnostico: Verificar "Nova Aba" e Seleção de Lojas
"""
import asyncio
from playwright.async_api import async_playwright

CPF = '14549094710'
SENHA = '161097'

async def login_and_navigate(page):
    """Login e navega para relatorio"""
    print("Efetuando login...")
    await page.goto('https://degustone.com.br/login')
    await page.wait_for_load_state('networkidle')
    await asyncio.sleep(2)
    # Login rapido
    await page.fill('input[name="username"]', CPF)
    btns = await page.query_selector_all('button.ant-btn.ant-btn-primary.ant-btn-lg:not(.btn-backspace)')
    dm = {}
    for b in btns:
        t = (await b.inner_text()).strip()
        if ' ou ' in t:
            for part in t.split(' ou '):
                d = part.strip()
                if d.isdigit(): dm[d] = b
    for d in SENHA:
        await dm[d].click()
    await page.click('button[type="submit"]')
    await page.wait_for_load_state('networkidle')
    await asyncio.sleep(3)
    print("Login concluido.")
    
    # Selecao Servidor/Franquia
    cbs = await page.query_selector_all('[role="combobox"]')
    if cbs:
        await cbs[0].click()
        await asyncio.sleep(0.5)
        await page.click('.multiselect__element') # Primeiro server
        await asyncio.sleep(1)
        
        await cbs[1].click()
        await asyncio.sleep(0.5)
        # Selecionar franquia 1866
        opts = await page.query_selector_all('.multiselect__element')
        for o in opts:
            if 'OFFICE' in (await o.inner_text()).upper():
                await o.click()
                break
        await asyncio.sleep(1)
        await page.click('button:has-text("Prosseguir")')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
    
    # Navegar
    print("Navegando para relatorio...")
    await page.evaluate('() => window.$nuxt.$router.push("/relatorio/despesas-loja")')
    await asyncio.sleep(4)
    
    # Popup
    xmark = await page.query_selector('.fa-xmark')
    if xmark and await xmark.is_visible():
        await xmark.click()
        await asyncio.sleep(1)

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Precisamos de permissao para popups se formos capturar nova aba, 
        # mas em headless default geralmente abre.
        context = await browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(30000)
        
        await login_and_navigate(page)

        # 1. SELECIONAR TODAS AS LOJAS
        print("\n--- TESTANDO SELECAO LOJAS ---")
        copy_btns = await page.query_selector_all('button:has(.anticon-copy)')
        if copy_btns:
            print("Botao multiloja encontrado. Clicando...")
            await copy_btns[0].click()
            await asyncio.sleep(2)
            await page.screenshot(path="debug_modal_aberto.png")
            print("Modal aberto (ver debug_modal_aberto.png)")
            
            # Tentar selecionar o checkbox do header
            print("Tentando clicar no checkbox 'Selecionar Todos'...")
            
            # Estrategia: Encontrar o checkbox no thead
            # Tentativa 1: Checkbox input
            checked = False
            header_input = await page.query_selector('.ant-modal-content .ant-table-thead input[type="checkbox"]')
            if header_input:
                await header_input.click(force=True)
                print("Click force=True no input")
                checked = True
            
            if not checked:
                # Tentativa 2: Wrapper
                header_wrapper = await page.query_selector('.ant-modal-content .ant-table-thead .ant-checkbox-wrapper')
                if header_wrapper:
                    await header_wrapper.click(force=True)
                    print("Click force=True no wrapper")
            
            await asyncio.sleep(1)
            await page.screenshot(path="debug_modal_selecionado.png")
            
            # Fechar modal
            print("Fechando modal...")
            await page.click('button:has-text("Fechar")')
            await asyncio.sleep(1)
        else:
            print("Botao multiloja nao encontrado!")

        # 2. CONFIGURAR DATA (para garantir que temos dados para consultar)
        # Vamos usar Jan/2025 para tentar pegar dados, ou periodo curto recente
        # Mas o foco aqui eh o comportamento do Consultar
        
        # 3. CONSULTAR - DETECTAR NOVA ABA (POPUP)
        print("\n--- TESTANDO CONSULTAR (NOVA ABA) ---")
        
        # Preparar para capturar popup
        async with context.expect_page() as new_page_info:
            print("Clicando em Consultar e aguardando nova pagina...")
            # Clicar Consultar
            btn = await page.query_selector('button:has-text("Consultar")')
            if btn:
                await btn.click(force=True)
            else:
                # Fallback JS
                await page.evaluate('''() => {
                    const btns = document.querySelectorAll('button');
                    for (const btn of btns) {
                        if (btn.textContent.includes('Consultar')) btn.click();
                    }
                }''')
        
        try:
            new_page = await new_page_info.value
            await new_page.wait_for_load_state()
            print(f"Nova pagina detectada! URL: {new_page.url}")
            await asyncio.sleep(3)
            await new_page.screenshot(path="debug_nova_aba.png")
            print("Screenshot da nova aba salvo: debug_nova_aba.png")
            
            content = await new_page.content()
            print(f"Conteudo da nova aba (size): {len(content)} bytes")
            
            await new_page.close()
            
        except Exception as e:
            print(f"Nenhuma nova aba foi detectada (ou timeout): {e}")
            # Se falhar, ver se o current page mudou ou mostrou erro
            await page.screenshot(path="debug_consultar_falha.png")

        await browser.close()

asyncio.run(run())
