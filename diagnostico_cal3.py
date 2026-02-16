"""
Script completo: Selecionar todas lojas, ativar Agrupar por Loja,
navegar calendario p/ jan/2025, e clicar Consultar.
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
        await asyncio.sleep(0.2)
    await page.click('button[type="submit"]')
    await page.wait_for_load_state('networkidle')
    await asyncio.sleep(5)
    
    cbs = await page.query_selector_all('[role="combobox"]')
    await cbs[0].click()
    await asyncio.sleep(1)
    opts = await page.query_selector_all('.multiselect__element')
    if opts: await opts[0].click()
    await asyncio.sleep(2)
    cbs = await page.query_selector_all('[role="combobox"]')
    await cbs[1].click()
    await asyncio.sleep(1)
    opts = await page.query_selector_all('.multiselect__element')
    for o in opts:
        t = (await o.inner_text()).strip()
        if 'OFFICE' in t.upper():
            await o.click()
            break
    await asyncio.sleep(1)
    await page.click('button:has-text("Prosseguir")')
    await page.wait_for_load_state('networkidle')
    await asyncio.sleep(5)
    
    await page.evaluate('() => window.$nuxt.$router.push("/relatorio/despesas-loja")')
    await asyncio.sleep(5)
    
    xmark = await page.query_selector('.fa-xmark')
    if xmark:
        vis = await xmark.is_visible()
        if vis:
            await xmark.click()
            await asyncio.sleep(1)
    
    print(f"Pronto: {page.url}")

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(30000)
        
        await login_and_navigate(page)

        # ========================================
        # 1. SELECIONAR TODAS AS LOJAS
        # ========================================
        print("\n=== 1. SELECIONAR TODAS AS LOJAS ===")
        
        # Clicar no botao copy (selecionar lojas) no header
        # btn[0] esta no contexto do header/Loja
        copy_btns = await page.query_selector_all('button:has(.anticon-copy)')
        if copy_btns:
            await copy_btns[0].click()
            await asyncio.sleep(2)
            print("Modal Multiloja aberto")

            # Screenshot do modal
            await page.screenshot(path="debug_multiloja.png")

            # Verificar quantas selecionadas
            footer_text = await page.evaluate('''() => {
                const els = document.querySelectorAll('*');
                for (const el of els) {
                    if (el.textContent.includes('Selecionada:') && el.offsetParent !== null) {
                        return el.textContent.trim().substring(0, 50);
                    }
                }
                return 'not found';
            }''')
            print(f"Antes: {footer_text}")

            # Clicar no checkbox do header para selecionar TODAS
            # O checkbox do header tem icone "-" (indeterminate)
            header_checkbox = await page.query_selector('th .ant-checkbox, thead .ant-checkbox-wrapper, thead .ant-checkbox')
            if header_checkbox:
                print("Checkbox header encontrado")
                await header_checkbox.click()
                await asyncio.sleep(1)
            else:
                # Tentar selecionar todos via primeiro checkbox na tabela
                all_checkboxes = await page.query_selector_all('.ant-checkbox-wrapper, .ant-checkbox')
                print(f"Checkboxes: {len(all_checkboxes)}")
                if all_checkboxes:
                    # O primeiro checkbox provavelmente e o "selecionar todos"
                    await all_checkboxes[0].click()
                    await asyncio.sleep(1)

            # Verificar quantas agora
            footer_text2 = await page.evaluate('''() => {
                const els = document.querySelectorAll('*');
                for (const el of els) {
                    if (el.textContent.includes('Selecionada:') && el.offsetParent !== null) {
                        return el.textContent.trim().substring(0, 50);
                    }
                }
                return 'not found';
            }''')
            print(f"Depois: {footer_text2}")
            
            await page.screenshot(path="debug_multiloja_all.png")

            # Se nao selecionou todas (ainda mostra :1), tentar outra abordagem
            if 'Selecionada: 1' in footer_text2 or footer_text2 == footer_text:
                print("Primeira tentativa nao selecionou todas, tentando checkbox indeterminate...")
                # Pode ser que precisemos clicar no primeiro checkbox do thead
                thead_inputs = await page.query_selector_all('thead input[type="checkbox"], thead .ant-checkbox-input')
                print(f"Thead checkbox inputs: {len(thead_inputs)}")
                if thead_inputs:
                    await thead_inputs[0].click(force=True)
                    await asyncio.sleep(1)
                else:
                    # Tentar via label
                    thead_labels = await page.query_selector_all('thead label')
                    print(f"Thead labels: {len(thead_labels)}")
                    if thead_labels:
                        await thead_labels[0].click(force=True)
                        await asyncio.sleep(1)

                # Re-verificar
                footer_text3 = await page.evaluate('''() => {
                    const body = document.body.textContent;
                    const match = body.match(/Selecionada:\\s*(\\d+)/);
                    return match ? match[1] : 'not found';
                }''')
                print(f"Selecionadas agora: {footer_text3}")
                await page.screenshot(path="debug_multiloja_check2.png")

            # Fechar modal
            try:
                await page.click('button:has-text("Fechar")')
                await asyncio.sleep(1)
                print("Modal fechado")
            except:
                await page.keyboard.press('Escape')
                await asyncio.sleep(1)

        # ========================================
        # 2. ATIVAR "AGRUPAR POR LOJA"
        # ========================================
        print("\n=== 2. ATIVAR AGRUPAR POR LOJA ===")
        
        # Identificar o switch de "Agrupar por Loja"
        # O label "Agrupar por Loja" esta ao lado do switch
        # Vou procurar via o texto
        agrupar_loja_switch = await page.evaluate('''() => {
            // Procurar pelo texto "Agrupar por Loja" e pegar o switch proximo
            const all = document.querySelectorAll('*');
            for (const el of all) {
                if (el.textContent.trim() === 'Agrupar por Loja' && el.offsetParent !== null) {
                    // Procurar switch no mesmo container
                    const parent = el.parentElement;
                    if (parent) {
                        const sw = parent.querySelector('.ant-switch');
                        if (sw) {
                            const rect = sw.getBoundingClientRect();
                            return { found: true, x: rect.x + rect.width/2, y: rect.y + rect.height/2 };
                        }
                    }
                }
            }
            return { found: false };
        }''')
        print(f"Switch Agrupar por Loja: {agrupar_loja_switch}")
        
        if agrupar_loja_switch.get('found'):
            await page.mouse.click(agrupar_loja_switch['x'], agrupar_loja_switch['y'])
            await asyncio.sleep(1)
            print("Toggle Agrupar por Loja clicado")
        else:
            # Fallback: pegar todos switches e identificar pelo contexto posicional
            # No formulario, "Agrupar por Loja" eh o segundo switch na linha do Periodo
            switches = await page.query_selector_all('.ant-switch')
            print(f"Switches: {len(switches)}")
            # Verificar posicao Y de cada switch para identificar
            for i, sw in enumerate(switches):
                vis = await sw.is_visible()
                if vis:
                    pos_y = await sw.evaluate('el => Math.round(el.getBoundingClientRect().y)')
                    checked = await sw.evaluate('el => el.classList.contains("ant-switch-checked")')
                    print(f"  switch[{i}]: y={pos_y} checked={checked}")

        await page.screenshot(path="debug_agrupar_loja.png")

        # ========================================
        # 3. NAVEGAR CALENDARIO ATE JAN/2025
        # ========================================
        print("\n=== 3. CONFIGURAR PERIODO JAN/2025 ===")
        
        # Abrir calendario
        cal_picker = await page.query_selector('.ant-calendar-picker')
        if cal_picker:
            await cal_picker.click(force=True)
            await asyncio.sleep(1)
            
            # Calendário actual: fev 2026 / mar 2026
            # Preciso ir para jan 2025
            # Clicar "<<" (prev year) 1 vez => fev 2025
            # Clicar "<" (prev month) 1 vez => jan 2025
            
            prev_year = await page.query_selector('.ant-calendar-prev-year-btn')
            prev_month = await page.query_selector('.ant-calendar-prev-month-btn')
            
            if prev_year:
                await prev_year.click()
                await asyncio.sleep(0.5)
                print("Retrocedeu 1 ano")
            
            if prev_month:
                await prev_month.click()
                await asyncio.sleep(0.5)
                print("Retrocedeu 1 mes")
            
            # Verificar mes/ano
            header_text = await page.evaluate('''() => {
                const years = document.querySelectorAll('.ant-calendar-year-select');
                const months = document.querySelectorAll('.ant-calendar-month-select');
                let result = [];
                months.forEach(m => result.push(m.textContent.trim()));
                years.forEach(y => result.push(y.textContent.trim()));
                return result;
            }''')
            print(f"Calendario agora: {header_text}")
            
            await page.screenshot(path="debug_calendario_jan2025.png")
            
            # Selecionar dia 1 de janeiro 2025
            # No range picker, o primeiro painel mostra jan 2025
            # Peciso selecionar dia 1 do primeiro painel
            clicked_day1 = await page.evaluate('''() => {
                // Pegar todas as celulas do calendario do primeiro painel
                const panels = document.querySelectorAll('.ant-calendar-range-part');
                if (panels.length < 1) return 'no panels';
                
                const leftPanel = panels[0];
                const cells = leftPanel.querySelectorAll('td.ant-calendar-cell');
                
                for (const cell of cells) {
                    const dateEl = cell.querySelector('.ant-calendar-date');
                    if (dateEl && dateEl.textContent.trim() === '1') {
                        // Verificar se nao eh de outro mes
                        if (!cell.classList.contains('ant-calendar-next-month-cell') && 
                            !cell.classList.contains('ant-calendar-last-month-cell')) {
                            dateEl.click();
                            return 'clicked day 1';
                        }
                    }
                }
                return 'day 1 not found';
            }''')
            print(f"Dia 1: {clicked_day1}")
            await asyncio.sleep(1)
            
            await page.screenshot(path="debug_dia1_selecionado.png")
            
            # Agora preciso selecionar a data final
            # Vou selecionar o dia 1 tambem (ou o ultimo dia do range)
            # Como eh um range picker, depois de selecionar data inicio,
            # o calendario espera a data final
            # Vou selecionar o mesmo dia 1 como data final
            # Ou simplesmente clicar no dia 1 de novo
            
            # Verificar se o calendario esta esperando data final
            await asyncio.sleep(1)
            
            # Selecionar data final = dia 1 tambem (mesmo periodo para teste)
            clicked_day1_end = await page.evaluate('''() => {
                const panels = document.querySelectorAll('.ant-calendar-range-part');
                if (panels.length < 1) return 'no panels';
                
                const leftPanel = panels[0];
                const cells = leftPanel.querySelectorAll('td.ant-calendar-cell');
                
                for (const cell of cells) {
                    const dateEl = cell.querySelector('.ant-calendar-date');
                    if (dateEl && dateEl.textContent.trim() === '1') {
                        if (!cell.classList.contains('ant-calendar-next-month-cell') && 
                            !cell.classList.contains('ant-calendar-last-month-cell')) {
                            dateEl.click();
                            return 'clicked day 1 end';
                        }
                    }
                }
                return 'day 1 not found';
            }''')
            print(f"Data final: {clicked_day1_end}")
            await asyncio.sleep(1)
            
            await page.screenshot(path="debug_datas_selecionadas.png")

            # Verificar valores dos inputs
            range_inputs = await page.query_selector_all('.ant-calendar-range-picker-input')
            for i, inp in enumerate(range_inputs):
                val = await inp.get_attribute('value') or ''
                print(f"  input[{i}]: '{val}'")

        # ========================================
        # 4. CLICAR CONSULTAR
        # ========================================
        print("\n=== 4. CONSULTAR ===")
        await page.click('button:has-text("Consultar")', force=True)
        print("Consultar clicado!")

        # Aguardar
        await asyncio.sleep(5)
        for attempt in range(6):
            spinners = await page.query_selector_all('.ant-spin-spinning')
            visible = sum(1 for s in spinners if asyncio.get_event_loop().run_until_complete(s.is_visible()) if True)
            # simpler approach
            break
        
        await asyncio.sleep(10)
        await page.screenshot(path="debug_resultado_final.png", full_page=True)
        print("Screenshot resultado: debug_resultado_final.png")
        
        # Verificar dados
        tbodies = await page.query_selector_all('tbody')
        theads = await page.query_selector_all('thead')
        print(f"Tabelas: {len(theads)} theads, {len(tbodies)} tbodies")
        
        for i, thead in enumerate(theads[:3]):
            ths = await thead.query_selector_all('th')
            texts = [await th.inner_text() for th in ths]
            print(f"  thead[{i}]: {[t.strip()[:15] for t in texts[:8]]}")

        for i, tbody in enumerate(tbodies[:3]):
            trs = await tbody.query_selector_all('tr')
            print(f"  tbody[{i}]: {len(trs)} linhas")
            for j, tr in enumerate(trs[:5]):
                tds = await tr.query_selector_all('td')
                texts = [await td.inner_text() for td in tds]
                print(f"    tr[{j}]: {[t.strip()[:20] for t in texts[:6]]}")

        # Verificar body text
        body = await page.inner_text('body')
        rs = body.count('R$')
        print(f"'R$' no body: {rs}")
        
        if 'Nenhum' in body:
            print("AVISO: Nenhum resultado")

        await browser.close()
        print("\n=== TESTE COMPLETO ===")

asyncio.run(run())
