"""
Diagnostico Reparo Total: Data (<< <) e Lojas (Select All)
Rodando e tirando screenshots de cada interacao.
"""
import asyncio
from playwright.async_api import async_playwright

CPF = '14549094710'
SENHA = '161097'

async def run():
    async with async_playwright() as p:
        # Browser visivel para debug (mas aqui rodamos no server, entao screenshots sao vitais)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        page.set_default_timeout(30000)
        
        print("1. Login...")
        await page.goto('https://degustone.com.br/login')
        await page.fill('input[name="username"]', CPF)
        
        # Senha virtual
        btns = await page.query_selector_all('button.ant-btn')
        dm = {}
        for b in btns:
            t = (await b.inner_text()).strip()
            if ' ou ' in t:
                for part in t.split(' ou '):
                    if part.strip().isdigit(): dm[part.strip()] = b
        for d in SENHA: await dm[d].click()
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        
        print("2. Selecao Franquia...")
        await page.click('[role="combobox"]') # Server
        await page.click('.multiselect__element') 
        await asyncio.sleep(1)
        
        cbs = await page.query_selector_all('[role="combobox"]')
        await cbs[1].click() # Franquia
        opts = await page.query_selector_all('.multiselect__element')
        for o in opts:
            if 'OFFICE' in (await o.inner_text()).upper():
                await o.click(); break
        await page.click('button:has-text("Prosseguir")')
        await asyncio.sleep(4)
        
        print("3. Navegando Relatorio...")
        # Fechar popups antes
        try: await page.click('.fa-xmark', timeout=2000)
        except: pass
        
        await page.evaluate('() => window.$nuxt.$router.push("/relatorio/despesas-loja")')
        await asyncio.sleep(4)
        try: await page.click('.fa-xmark', timeout=2000)
        except: pass

        # --- DIAGNOSTICO DATA (<< e <) ---
        print("\n--- TESTE DATA VISUAL ---")
        await page.screenshot(path="diag_0_antes_calendario.png")
        
        picker = await page.query_selector('.ant-calendar-picker')
        if picker:
            await picker.click(force=True)
            await asyncio.sleep(1)
            await page.screenshot(path="diag_1_calendario_aberto.png")
            
            # Verificar ano atual
            year_el = await page.query_selector('.ant-calendar-year-select')
            current_year = await year_el.inner_text() if year_el else 'Unknown'
            print(f"Ano Inicial: {current_year}")

            # Tentar clicar no << (.ant-calendar-prev-year-btn)
            prev_year_btn = await page.query_selector('.ant-calendar-prev-year-btn')
            if prev_year_btn:
                print("Botao '<<' (Ano Anterior) encontrado. Clicando...")
                await prev_year_btn.click()
                await asyncio.sleep(1)
                await page.screenshot(path="diag_2_apos_click_ano.png")
                
                year_el = await page.query_selector('.ant-calendar-year-select')
                new_year = await year_el.inner_text() if year_el else 'Unknown'
                print(f"Ano Apos Clique: {new_year}")
            else:
                print("Botao '<<' NAO ENCONTRADO!")

            # Tentar clicar no < (.ant-calendar-prev-month-btn)
            prev_month_btn = await page.query_selector('.ant-calendar-prev-month-btn')
            if prev_month_btn:
                print("Botao '<' (Mes Anterior) encontrado. Clicando...")
                await prev_month_btn.click()
                await asyncio.sleep(1)
                await page.screenshot(path="diag_3_apos_click_mes.png")
            else:
                 print("Botao '<' NAO ENCONTRADO!")
            
            # Tentar clicar dia 1
            print("Clicando dia 1...")
            # Pega o primeiro '1' que nao seja last-month
            await page.evaluate('''() => {
                const tds = document.querySelectorAll('.ant-calendar-table td');
                for (const td of tds) {
                    if (td.innerText.trim() == '1' && !td.classList.contains('ant-calendar-last-month-cell')) {
                        td.click();
                        return;
                    }
                }
            }''')
            await asyncio.sleep(1)
            await page.screenshot(path="diag_4_apos_click_dia.png")
            
        else:
            print("Picker nao encontrado!")

        # --- DIAGNOSTICO LOJAS ---
        print("\n--- TESTE LOJAS ---")
        copy_btns = await page.query_selector_all('button:has(.anticon-copy)')
        if copy_btns:
            await copy_btns[0].click()
            await asyncio.sleep(2)
            await page.screenshot(path="diag_5_modal_lojas.png")
            
            modal = await page.query_selector('.ant-modal-content')
            if modal:
                # Tentar identificar o checkbox do header
                # Vamos listar classes de todos os inputs checkbox
                print("Procurando checkboxes...")
                checks = await modal.query_selector_all('input[type="checkbox"]')
                print(f"Total inputs checkbox encontrados: {len(checks)}")
                
                # Tentar clicar no primeiro (geralmente header)
                if len(checks) > 0:
                    print("Clicando no primeiro checkbox (Header?)...")
                    # Clicar no wrapper pai se possivel, ou input force
                    await checks[0].click(force=True)
                    await asyncio.sleep(1)
                    await page.screenshot(path="diag_6_apos_click_header.png")
                    
                    # Validar
                    checked = await modal.query_selector_all('.ant-checkbox-checked')
                    print(f"Checkboxes marcados apos clique: {len(checked)}")
            
            await page.click('button:has-text("Fechar")')
        else:
            print("Botao Lojas nao encontrado")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(run())
