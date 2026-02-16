"""
Script de Correcao: Focado em acertar o clique no checkbox 'Selecionar Todos' do modal Multiloja.
"""
import asyncio
from playwright.async_api import async_playwright

CPF = '14549094710'
SENHA = '161097'

async def login_and_navigate(page):
    """Login e navega para relatorio"""
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
        page = await browser.new_page()
        page.set_default_timeout(30000)
        
        await login_and_navigate(page)
        print("Navegacao concluida")

        # 1. SELECIONAR TODAS AS LOJAS (CORRIGIDO)
        print("\n--- SELECIONANDO LOJAS ---")
        copy_btns = await page.query_selector_all('button:has(.anticon-copy)')
        if copy_btns:
            await copy_btns[0].click()
            await asyncio.sleep(2)
            print("Modal aberto")
            
            # Tentar selecionar o checkbox do header com seletores mais especificos
            # O modal deve ter uma tabela
            # Ant Design table header checkbox: .ant-table-thead > tr > th.ant-table-selection-column > span > div > label > span > input
            
            # Estrategia 1: Clicar no primeiro checkbox visivel dentro do modal
            modal = await page.query_selector('.ant-modal-content')
            if modal:
                # Buscar checkboxes dentro do modal
                checkboxes = await modal.query_selector_all('.ant-checkbox-input, input[type="checkbox"]')
                print(f"Checkboxes encontrados no modal: {len(checkboxes)}")
                
                if checkboxes:
                    # O primeiro deve ser o do header
                    print("Clicando no primeiro checkbox (header)...")
                    # O input pode estar escondido (opacity 0), entao clicamos no parent wrapper ou label
                    # Mas force=True no input costuma funcionar
                    await checkboxes[0].click(force=True)
                    await asyncio.sleep(1)
                else:
                    print("Nenhum checkbox input achado. Tentando labels classes ant-checkbox")
                    wrappers = await modal.query_selector_all('.ant-checkbox')
                    if wrappers:
                        await wrappers[0].click()
                        await asyncio.sleep(1)

            # Verificar selecao
            footer_text = await page.evaluate('''() => {
                const els = document.querySelectorAll('*');
                for (const el of els) {
                    if (el.textContent.includes('Selecionada:') && el.offsetParent !== null) {
                        return el.textContent.trim().substring(0, 50);
                    }
                }
                return 'not found';
            }''')
            print(f"Status selecao: {footer_text}")
            
            # Se ainda for 1, tentar clicar no segundo checkbox (as vezes o primeiro eh hidden ou fantasma)
            if 'Selecionada: 1' in footer_text or 'Selecionada: 0' in footer_text:
                print("Tentativa 2: Clicando no wrapper do checkbox do header via classe")
                # .ant-table-header .ant-checkbox-wrapper
                header_cb = await page.query_selector('.ant-modal .ant-table-thead .ant-checkbox-wrapper')
                if header_cb:
                    await header_cb.click(force=True)
                    await asyncio.sleep(1)
                    
            # Verificar selecao 2
            footer_text2 = await page.evaluate('''() => {
                const els = document.querySelectorAll('*');
                for (const el of els) {
                    if (el.textContent.includes('Selecionada:') && el.offsetParent !== null) {
                        return el.textContent.trim().substring(0, 50);
                    }
                }
                return 'not found';
            }''')
            print(f"Status selecao final: {footer_text2}")
            
            # Fechar modal
            await page.click('button:has-text("Fechar")')
            await asyncio.sleep(1)

        # 2. AGRUPAR POR LOJA
        print("\n--- AGRUPAR POR LOJA ---")
        # Identificar switch pelo label
        agrupar_ok = await page.evaluate('''() => {
            const els = document.querySelectorAll('label, div, span');
            for (const el of els) {
                if (el.textContent.trim() === 'Agrupar por Loja') {
                    const parent = el.parentElement;
                    if (parent) {
                        const sw = parent.querySelector('.ant-switch');
                        if (sw) {
                            sw.click();
                            return true;
                        }
                    }
                }
            }
            return false;
        }''')
        print(f"Switch clicado via JS: {agrupar_ok}")
        await asyncio.sleep(1)

        # 3. CALENDARIO JAN/2025
        print("\n--- CALENDARIO ---")
        cal_picker = await page.query_selector('.ant-calendar-picker')
        await cal_picker.click()
        await asyncio.sleep(1)
        
        # Retroceder 1 ano + 1 mes
        await page.click('.ant-calendar-prev-year-btn')
        await asyncio.sleep(0.5)
        await page.click('.ant-calendar-prev-month-btn')
        await asyncio.sleep(0.5)
        
        # Clicar dia 1 (duas vezes para fechar range, por seguranca)
        # Selecionar dia 1 do primeiro painel
        await page.evaluate('''() => {
            const panels = document.querySelectorAll('.ant-calendar-range-part');
            const leftPanel = panels[0];
            const cells = leftPanel.querySelectorAll('td.ant-calendar-cell');
            for (const cell of cells) {
                const dateEl = cell.querySelector('.ant-calendar-date');
                if (dateEl && dateEl.textContent.trim() === '1') {
                     if (!cell.classList.contains('ant-calendar-next-month-cell') && 
                         !cell.classList.contains('ant-calendar-last-month-cell')) {
                        dateEl.click(); // Data inicio
                        setTimeout(() => dateEl.click(), 500); // Data fim (mesmo dia)
                        return;
                    }
                }
            }
        }''')
        await asyncio.sleep(2)
        
        # Screenshot final antes de consultar
        await page.screenshot(path="debug_config_final.png")
        
        # 4. CONSULTAR
        print("\n--- CONSULTAR ---")
        await page.click('button:has-text("Consultar")', force=True)
        await asyncio.sleep(5)
        
        await page.screenshot(path="debug_resultado_tabela.png")
        print("Teste finalizado")
        
        await browser.close()

asyncio.run(run())
