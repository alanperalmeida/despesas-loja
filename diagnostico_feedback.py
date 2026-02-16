"""
Diagnostico: Validar Range de Datas e Selecao de Todas as Lojas
"""
import asyncio
from playwright.async_api import async_playwright

CPF = '14549094710'
SENHA = '161097'

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # Visivel para debug
        context = await browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(30000)
        
        # 1. Login
        print("Login...")
        await page.goto('https://degustone.com.br/login')
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
        await asyncio.sleep(2)
        
        # 2. Selecionar Contexto (Producao / Office)
        print("Selecionando Franquia...")
        cbs = await page.query_selector_all('[role="combobox"]')
        if cbs:
            await cbs[0].click() # Servidor
            await page.click('.multiselect__element')
            await asyncio.sleep(0.5)
            
            await cbs[1].click() # Franquia
            # Selecionar uma qualquer, exemplo OFFICE ou 1866
            opts = await page.query_selector_all('.multiselect__element')
            for o in opts:
                if 'OFFICE' in (await o.inner_text()).upper():
                    await o.click()
                    break
            
            await page.click('button:has-text("Prosseguir")')
            await asyncio.sleep(4)
            
        # 3. Navegar Relatorio
        print("Navegando para relatorio...")
        await page.evaluate('() => window.$nuxt.$router.push("/relatorio/despesas-loja")')
        await asyncio.sleep(4)
        
        # Fechar popup
        try:
            await page.click('.fa-xmark')
        except: pass

        # 4. TESTAR DATA RANGE (01/01/2025 a 28/02/2025)
        print("\n--- TESTANDO DATA ---")
        DATA_INICIO = '01/01/2025'
        DATA_FIM = '28/02/2025'
        
        range_picker = await page.query_selector('.ant-calendar-picker')
        if range_picker:
            await range_picker.click(force=True)
            await asyncio.sleep(1)
            
            # Tentar digitacao primeiro (padrao)
            print("Tentando digitar datas...")
            inputs = await page.query_selector_all('.ant-calendar-range-picker-input')
            if len(inputs) >= 2:
                # Inicio
                await inputs[0].click()
                await page.keyboard.press('Control+A')
                await page.keyboard.press('Backspace')
                await page.keyboard.type(DATA_INICIO)
                await page.keyboard.press('Tab')
                
                # Fim
                await inputs[1].click()
                await page.keyboard.press('Control+A')
                await page.keyboard.press('Backspace')
                await page.keyboard.type(DATA_FIM)
                await page.keyboard.press('Enter')
                await asyncio.sleep(2)
                
            await page.screenshot(path="debug_dates_typed.png")
            print("Screenshot digitacao: debug_dates_typed.png")

        # 5. TESTAR SELECAO DE LOJAS
        print("\n--- TESTANDO LOJAS ---")
        copy_btns = await page.query_selector_all('button:has(.anticon-copy)')
        if copy_btns:
            await copy_btns[0].click()
            await asyncio.sleep(2)
            
            print("Modal aberto. Verificando checkboxes...")
            modal = await page.query_selector('.ant-modal-content')
            
            # Tentar clicar no 'Select All' header
            print("Clicando Select All (Header)...")
            header_chk = await modal.query_selector('.ant-table-thead .ant-table-selection-column .ant-checkbox-wrapper')
            if header_chk:
                await header_chk.click(force=True)
            else:
                print("Header check nao encontrado!")
                
            await asyncio.sleep(1)
            await page.screenshot(path="debug_stores_selected.png")
            
            # Validar quantos estao selecionados
            checked = await modal.query_selector_all('.ant-table-tbody .ant-checkbox-checked')
            total = await modal.query_selector_all('.ant-table-tbody .ant-checkbox-wrapper')
            print(f"Lojas Selecionadas: {len(checked)} / {len(total)}")
            
            # Se nao marcou todos, tentar um por um
            if len(checked) < len(total):
                print("Falha no Select All. Tentando iterar...")
                for chk in total:
                    if not await chk.is_checked(): # nao tem esse metodo direto wrapper, tem que ver classe
                        if 'ant-checkbox-checked' not in await chk.get_attribute('class'):
                            await chk.click()
            
            await page.screenshot(path="debug_stores_iterated.png")
            
        await browser.close()

if __name__ == '__main__':
    asyncio.run(run())
