"""
Diagnostico: Navegar no calendario ate jan/2025, ativar Agrupar por Loja,
e selecionar todas as lojas.
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
        print("\n--- SELECIONANDO TODAS AS LOJAS ---")
        
        # O botao ao lado do dropdown Loja no header com icone de copiar
        # Esse botao parece ser "selecionar todas as lojas"
        # Primeiro, vamos verificar o header
        header_loja = await page.evaluate('''() => {
            // Procurar pelo texto "Loja" no header
            const labels = document.querySelectorAll('label, span, div');
            for (const el of labels) {
                if (el.textContent.trim() === 'Loja :' || el.textContent.trim() === 'Loja:') {
                    const parent = el.parentElement;
                    return parent ? parent.innerHTML.substring(0, 200) : 'no parent';
                }
            }
            return 'Loja label nao encontrado';
        }''')
        print(f"Loja header context: {header_loja[:100]}")

        # Clicar no botao de selecionar todos (o icone copy ao lado do Loja)
        # O botao esta ao lado do dropdown "VIA BRASIL [1000]"
        loja_btn = await page.query_selector_all('button:has(.anticon-copy)')
        print(f"Botoes copy: {len(loja_btn)}")
        
        # O primeiro botao copy visivel provavelmente esta no header proximo a "Loja"
        if loja_btn:
            # Vamos pegar info do pai de cada botao
            for i, btn in enumerate(loja_btn[:3]):
                vis = await btn.is_visible()
                parent_info = await btn.evaluate('''el => {
                    let p = el.parentElement;
                    let gp = p ? p.parentElement : null;
                    return {
                        parent: p ? p.textContent.substring(0, 50) : '',
                        grandparent: gp ? gp.textContent.substring(0, 50) : '',
                        parentTag: p ? p.tagName : ''
                    };
                }''')
                print(f"  btn[{i}]: vis={vis} parent='{parent_info['parent'][:30]}' gp='{parent_info['grandparent'][:30]}' tag={parent_info['parentTag']}")

        # O botao copy no header proximo ao "Loja" - eh o PRIMEIRO botao visivel
        # Vamos clica-lo para ver o que faz
        if len(loja_btn) > 0:
            first_copy = loja_btn[0]
            vis = await first_copy.is_visible()
            if vis:
                print("Clicando botao copy do header (Loja)...")
                await first_copy.click()
                await asyncio.sleep(2)
                
                # Verificar se abriu dropdown ou modal
                await page.screenshot(path="debug_loja_select_all.png")
                print("Screenshot: debug_loja_select_all.png")
                
                # Verificar o valor atual do Loja
                loja_text = await page.evaluate('''() => {
                    const els = document.querySelectorAll('.ant-select-selection-selected-value, .ant-select-selection__rendered');
                    return Array.from(els).map(e => e.textContent.substring(0, 50));
                }''')
                print(f"Loja apos clicar: {loja_text}")

        # ========================================
        # 2. ABRIR DROPDOWN LOJA E LISTAR OPCOES
        # ========================================
        print("\n--- ABRINDO DROPDOWN LOJA ---")
        # Tentar clicar no dropdown "VIA BRASIL [1000]"
        # Pode ser um ant-select customizado
        loja_dropdown = await page.evaluate('''() => {
            // Procurar o element que contem "VIA BRASIL"
            const all = document.querySelectorAll('*');
            for (const el of all) {
                if (el.textContent.includes('VIA BRASIL') && 
                    el.offsetParent !== null &&
                    (el.classList.contains('ant-select') || 
                     el.closest('.ant-select') ||
                     el.tagName === 'SELECT')) {
                    return {
                        tag: el.tagName,
                        cls: el.className.substring(0, 60),
                        text: el.textContent.substring(0, 50),
                        hasSelect: !!el.closest('.ant-select')
                    };
                }
            }
            return null;
        }''')
        print(f"Loja dropdown: {loja_dropdown}")

        # Tentar encontrar e clicar usando seletor mais generico
        loja_el = await page.query_selector('text=VIA BRASIL')
        if loja_el:
            parent_cls = await loja_el.evaluate('el => el.parentElement ? el.parentElement.className : "no parent"')
            print(f"VIA BRASIL parent cls: {parent_cls[:60]}")
            await loja_el.click()
            await asyncio.sleep(2)
            
            # Verificar dropdown
            dropdown_menu = await page.query_selector_all('.ant-select-dropdown-menu-item')
            print(f"Dropdown items apos click: {len(dropdown_menu)}")
            for i, item in enumerate(dropdown_menu[:10]):
                text = await item.inner_text()
                print(f"  [{i}] {text.strip()[:40]}")
            
            await page.screenshot(path="debug_loja_opened.png")

        # ========================================
        # 3. ATIVAR TOGGLE "AGRUPAR POR LOJA"
        # ========================================
        print("\n--- ATIVANDO AGRUPAR POR LOJA ---")
        
        # Identificar o switch correto
        # Os switches/toggles estao organizados no formulario
        # "Agrupar" e "Agrupar por Loja" estao ao lado do Periodo
        switches = await page.query_selector_all('.ant-switch')
        print(f"Total switches: {len(switches)}")
        
        # Identificar cada switch pelo contexto
        for i, sw in enumerate(switches):
            vis = await sw.is_visible()
            checked = await sw.evaluate('el => el.classList.contains("ant-switch-checked")')
            
            # Pegar texto do label mais proximo
            label_info = await sw.evaluate('''el => {
                // Pegar o texto do pai e irmãos
                let parent = el.parentElement;
                let grandparent = parent ? parent.parentElement : null;
                let ggp = grandparent ? grandparent.parentElement : null;
                
                let result = [];
                if (parent) result.push('p:' + parent.textContent.substring(0, 30));
                if (grandparent) result.push('gp:' + grandparent.textContent.substring(0, 40));
                
                // Procurar label anterior
                let prev = el.previousElementSibling;
                while (prev) {
                    let t = prev.textContent.trim();
                    if (t) { result.push('prev:' + t.substring(0, 30)); break; }
                    prev = prev.previousElementSibling;
                }
                
                // Verificar posicao na pagina
                let rect = el.getBoundingClientRect();
                result.push('y:' + Math.round(rect.y));
                
                return result.join(' | ');
            }''')
            
            if vis:
                print(f"  switch[{i}]: checked={checked} {label_info[:80]}")

        # ========================================
        # 4. NAVEGAR CALENDARIO ATE JAN/2025
        # ========================================
        print("\n--- NAVEGANDO CALENDARIO ---")
        
        # Abrir calendario
        cal_picker = await page.query_selector('.ant-calendar-picker')
        if cal_picker:
            await cal_picker.click(force=True)
            await asyncio.sleep(1)
            
            # Verificar mes/ano atual
            year_btn = await page.query_selector('.ant-calendar-year-select')
            month_btn = await page.query_selector('.ant-calendar-month-select')
            if year_btn and month_btn:
                year_text = await year_btn.inner_text()
                month_text = await month_btn.inner_text()
                print(f"Calendario atual: {month_text} {year_text}")

            # Clicar "<<" (prev year) para ir a 2025
            prev_year_btn = await page.query_selector('.ant-calendar-prev-year-btn')
            if prev_year_btn:
                await prev_year_btn.click()
                await asyncio.sleep(0.5)
                year_text = await year_btn.inner_text()
                month_text = await month_btn.inner_text()
                print(f"Apos prev year: {month_text} {year_text}")
                
                # Agora preciso ir para janeiro
                # Se estamos em fev 2025, precisamos ir 1 mes atras
                prev_month_btn = await page.query_selector('.ant-calendar-prev-month-btn')
                if prev_month_btn:
                    await prev_month_btn.click()
                    await asyncio.sleep(0.5)
                    year_text = await year_btn.inner_text()
                    month_text = await month_btn.inner_text()
                    print(f"Apos prev month: {month_text} {year_text}")

            await page.screenshot(path="debug_calendario_jan2025.png")
            print("Screenshot: debug_calendario_jan2025.png")
            
            # Clicar no dia 1
            # Procurar as celulas do calendario
            day_cells = await page.query_selector_all('.ant-calendar-date')
            print(f"Celulas de dia: {len(day_cells)}")
            
            for cell in day_cells:
                text = await cell.inner_text()
                if text.strip() == '1':
                    # Verificar se eh do mes atual (nao do proximo/anterior)
                    parent_td = await cell.evaluate('''el => {
                        let td = el.closest('td');
                        return td ? td.className : '';
                    }''')
                    if 'next-month' not in parent_td and 'last-month' not in parent_td:
                        print(f"Clicando dia 1 (cls: {parent_td[:40]})")
                        await cell.click()
                        await asyncio.sleep(1)
                        break
            
            # Agora preciso selecionar data final tambem
            # No range picker, apos clicar data inicio,
            # precisa clicar data final
            # Vamos clicar na data de hoje (13/02/2026) ou
            # simplesmente usar o mesmo dia como fim
            
            await page.screenshot(path="debug_calendario_dia1.png")
            print("Screenshot apos selecionar dia 1: debug_calendario_dia1.png")

        await asyncio.sleep(2)
        await page.screenshot(path="debug_final.png", full_page=True)
        
        await browser.close()
        print("\n=== DIAGNOSTICO COMPLETO ===")

asyncio.run(run())
