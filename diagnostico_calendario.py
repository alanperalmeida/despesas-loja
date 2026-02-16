"""
Diagnostico: Explorar o calendário, toggle Agrupar por Loja, e seletor de Loja
para entender como interagir com esses elementos.
"""
import asyncio
from playwright.async_api import async_playwright

CPF = '14549094710'
SENHA = '161097'

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(30000)

        # === LOGIN ===
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
        print(f"Login: {page.url}")

        # === SERVIDOR + FRANQUIA ===
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
                print(f"Franquia: {t}")
                break
        await asyncio.sleep(1)
        await page.click('button:has-text("Prosseguir")')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(5)

        # === NAVEGAR PARA RELATORIO ===
        await page.evaluate('() => window.$nuxt.$router.push("/relatorio/despesas-loja")')
        await asyncio.sleep(5)
        print(f"Relatorio: {page.url}")

        # === FECHAR POPUP ===
        xmark = await page.query_selector('.fa-xmark')
        if xmark:
            vis = await xmark.is_visible()
            if vis:
                await xmark.click()
                await asyncio.sleep(1)
                print("Popup fechado")

        # ========================================
        # EXPLORAR ELEMENTOS DO FORMULARIO
        # ========================================
        print("\n" + "="*60)
        print("EXPLORANDO FORMULARIO DE RELATORIO")
        print("="*60)

        # 1. CALENDARIO / DATE PICKER
        print("\n--- CALENDARIO ---")
        cal_pickers = await page.query_selector_all('.ant-calendar-picker')
        print(f"Calendar pickers: {len(cal_pickers)}")
        
        range_inputs = await page.query_selector_all('.ant-calendar-range-picker-input')
        print(f"Range inputs: {len(range_inputs)}")
        for i, inp in enumerate(range_inputs):
            val = await inp.get_attribute('value') or ''
            placeholder = await inp.get_attribute('placeholder') or ''
            print(f"  input[{i}]: value='{val}' placeholder='{placeholder}'")

        # Clicar no calendario para abrir
        if cal_pickers:
            await cal_pickers[0].click(force=True)
            await asyncio.sleep(2)
            await page.screenshot(path="debug_calendario_aberto.png")
            print("Screenshot: debug_calendario_aberto.png")

            # Ver a estrutura do calendario aberto
            cal_panels = await page.query_selector_all('.ant-calendar-panel, .ant-calendar-range')
            print(f"Calendar panels: {len(cal_panels)}")

            # Botoes de navegacao do calendario
            nav_btns = await page.query_selector_all('.ant-calendar-prev-year-btn, .ant-calendar-next-year-btn, .ant-calendar-prev-month-btn, .ant-calendar-next-month-btn')
            print(f"Nav buttons: {len(nav_btns)}")
            for i, btn in enumerate(nav_btns):
                cls = await btn.get_attribute('class') or ''
                title = await btn.get_attribute('title') or ''
                text = await btn.inner_text()
                print(f"  nav[{i}]: cls='{cls[:50]}' title='{title}' text='{text.strip()[:20]}'")

            # Header do calendario (mes/ano atual)
            month_selects = await page.query_selector_all('.ant-calendar-month-select, .ant-calendar-year-select')
            for ms in month_selects:
                text = await ms.inner_text()
                print(f"  Month/Year: '{text.strip()}'")

            # Tags de atalho (Hoje, Ontem, etc.)
            tags = await page.query_selector_all('.ant-tag')
            print(f"Tags de atalho: {len(tags)}")
            for tag in tags:
                text = await tag.inner_text()
                vis = await tag.is_visible()
                cls = await tag.get_attribute('class') or ''
                if vis:
                    print(f"  tag: '{text.strip()}' cls='{cls[:40]}'")

            # Fechar calendario (clicar em outro lugar)
            await page.keyboard.press('Escape')
            await asyncio.sleep(1)

        # 2. TOGGLES (SWITCHES)
        print("\n--- TOGGLES/SWITCHES ---")
        switches = await page.query_selector_all('.ant-switch, button[role="switch"]')
        print(f"Switches: {len(switches)}")
        for i, sw in enumerate(switches):
            checked = await sw.get_attribute('aria-checked')
            cls = await sw.get_attribute('class') or ''
            # Pegar label proximo
            parent_text = await sw.evaluate('el => { let p = el.parentElement; return p ? p.textContent.substring(0, 80) : ""; }')
            label = await sw.evaluate('''el => {
                let prev = el.previousElementSibling;
                let next = el.nextElementSibling;
                let parent = el.parentElement;
                let labels = [];
                if (prev) labels.push('prev:' + prev.textContent.substring(0, 30));
                if (next) labels.push('next:' + next.textContent.substring(0, 30));
                // Tbm procurar no pai
                let allText = parent ? parent.textContent.substring(0, 50) : '';
                labels.push('parent:' + allText);
                return labels.join(' | ');
            }''')
            print(f"  switch[{i}]: checked={checked} cls='{cls[:40]}' label='{label[:80]}'")

        # 3. SELETOR DE LOJA (no header)
        print("\n--- SELETOR DE LOJA ---")
        # No header tem um dropdown "Loja: VIA BRASIL [1000]"
        loja_select = await page.query_selector_all('.ant-select')
        print(f"Ant selects: {len(loja_select)}")
        for i, sel in enumerate(loja_select):
            vis = await sel.is_visible()
            text = await sel.inner_text()
            cls = await sel.get_attribute('class') or ''
            print(f"  select[{i}]: vis={vis} text='{text.strip()[:40]}' cls='{cls[:50]}'")

        # Tambem o botao ao lado do dropdown de Loja (icone de copiar/selecionar todos)
        copy_btns = await page.query_selector_all('.anticon-copy, button:has(.anticon-copy)')
        print(f"Copy/Select-all buttons: {len(copy_btns)}")
        for i, btn in enumerate(copy_btns):
            vis = await btn.is_visible()
            parent_text = await btn.evaluate('el => el.parentElement.textContent.substring(0, 30)')
            print(f"  copy[{i}]: vis={vis} parent='{parent_text}'")

        # Verificar o select no header (Loja)
        header_selects = await page.evaluate('''() => {
            const selects = document.querySelectorAll('.ant-select');
            return Array.from(selects).map(s => ({
                text: s.textContent.substring(0, 50),
                cls: s.className.substring(0, 60),
                visible: s.offsetParent !== null,
                open: s.classList.contains('ant-select-open')
            }));
        }''')
        print(f"\nDetailed selects:")
        for i, s in enumerate(header_selects):
            print(f"  [{i}] text='{s['text'][:40]}' visible={s['visible']} open={s['open']} cls='{s['cls'][:50]}'")

        # Screenshot da pagina completa
        await page.screenshot(path="debug_formulario.png", full_page=True)
        print("\nScreenshot formulario: debug_formulario.png")

        # 4. Clicar no dropdown de Loja no header para ver opcoes
        print("\n--- ABRINDO SELETOR DE LOJA ---")
        # O seletor de Loja no header - tentar clicar no ant-select que tem "VIA BRASIL"
        for i, sel in enumerate(loja_select):
            text = await sel.inner_text()
            vis = await sel.is_visible()
            if vis and ('BRASIL' in text.upper() or 'LOJA' in text.upper() or '1000' in text):
                print(f"Clicando no select[{i}]: '{text.strip()[:40]}'")
                await sel.click()
                await asyncio.sleep(2)
                break

        # Ver opcoes do dropdown
        dropdown_items = await page.query_selector_all('.ant-select-dropdown-menu-item, .ant-select-item')
        print(f"Dropdown items: {len(dropdown_items)}")
        for i, item in enumerate(dropdown_items[:10]):
            text = await item.inner_text()
            selected = await item.get_attribute('aria-selected')
            cls = await item.get_attribute('class') or ''
            print(f"  item[{i}]: '{text.strip()[:40]}' selected={selected} cls='{cls[:50]}'")

        await page.screenshot(path="debug_loja_dropdown.png")
        print("Screenshot loja dropdown: debug_loja_dropdown.png")

        # Fechar dropdown
        await page.keyboard.press('Escape')
        await asyncio.sleep(1)

        # 5. Verificar botao de "selecionar todos" ao lado do Loja
        print("\n--- BOTAO SELECIONAR TODOS (LOJA) ---")
        # O icone de copiar ao lado do select de Loja pode ser "selecionar todos"
        all_btns = await page.query_selector_all('button')
        for i, btn in enumerate(all_btns):
            vis = await btn.is_visible()
            if vis:
                inner = await btn.inner_html()
                text = await btn.inner_text()
                if 'copy' in inner.lower() or 'anticon-copy' in inner.lower():
                    parent_text = await btn.evaluate('el => el.parentElement.textContent.substring(0, 40)')
                    print(f"  btn[{i}]: text='{text[:20]}' parent='{parent_text}' html contains 'copy'")

        await browser.close()
        print("\n=== DIAGNOSTICO COMPLETO ===")

asyncio.run(run())
