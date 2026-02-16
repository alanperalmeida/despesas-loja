"""
Diagnostico v3: Focar na pagina de selecao de servidor/franquia
Interagir com os Ant Design selects
"""
import asyncio
from playwright.async_api import async_playwright

CPF = '14549094710'
SENHA = '161097'
BASE_URL = 'https://degustone.com.br'

async def login(page):
    """Login no sistema"""
    await page.goto(f"{BASE_URL}/login")
    await page.wait_for_load_state('networkidle')
    await asyncio.sleep(2)

    await page.fill('input[name="username"]', CPF)

    buttons = await page.query_selector_all(
        'button.ant-btn.ant-btn-primary.ant-btn-lg:not(.btn-backspace)'
    )
    digit_map = {}
    for btn in buttons:
        text = (await btn.inner_text()).strip()
        if ' ou ' in text:
            for part in text.split(' ou '):
                d = part.strip()
                if d.isdigit():
                    digit_map[d] = btn

    for digito in SENHA:
        await digit_map[digito].click()
        await asyncio.sleep(0.2)

    await page.click('button[type="submit"]')
    await page.wait_for_load_state('networkidle')
    await asyncio.sleep(5)
    print(f"Login OK. URL: {page.url}")

async def diagnosticar_v3():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(30000)

        await login(page)

        # ====== PAGINA DE SELECAO ======
        print("\n--- ESTRUTURA DA PAGINA DE SELECAO ---")

        # Detalhar TODA a estrutura HTML dos campos Servidor e Franquia
        # Procurar elementos com role="combobox" (Ant Select)
        comboboxes = await page.query_selector_all('[role="combobox"]')
        print(f"Comboboxes: {len(comboboxes)}")
        for i, cb in enumerate(comboboxes):
            html = await cb.evaluate('el => el.outerHTML')
            print(f"  combobox[{i}]: {html[:200]}")

        # Procurar Ant Select triggers
        select_selectors = await page.query_selector_all(
            '.ant-select-selector, .ant-select-selection, .ant-select'
        )
        print(f"\nAnt Select elements: {len(select_selectors)}")
        for i, sel in enumerate(select_selectors):
            cls = await sel.get_attribute('class') or ''
            text = await sel.inner_text()
            role = await sel.get_attribute('role') or ''
            vis = await sel.is_visible()
            html = await sel.evaluate('el => el.outerHTML.substring(0, 300)')
            print(f"  [{i}] cls='{cls[:60]}' text='{text.strip()[:40]}' role='{role}' visible={vis}")
            print(f"       html={html[:200]}")

        # Procurar todas as divs filhas do card principal
        print("\n--- CONTEUDO DO CARD ---")
        card_body = await page.query_selector('.ant-card-body')
        if card_body:
            inner = await card_body.inner_html()
            # Salvar HTML do card
            with open("debug_card_body.html", "w", encoding="utf-8") as f:
                f.write(inner)
            print(f"HTML do card body salvo (tamanho: {len(inner)} chars)")

            # Listar filhos diretos
            children = await card_body.query_selector_all('*')
            print(f"Filhos do card body: {len(children)}")
            for i, child in enumerate(children[:30]):
                tag = await child.evaluate('el => el.tagName')
                cls = await child.get_attribute('class') or ''
                text = await child.inner_text()
                vis = await child.is_visible()
                if vis and text.strip():
                    print(f"  [{i}] {tag} cls='{cls[:50]}' text='{text.strip()[:60]}'")

        # Tentar clicar no select de Servidor
        print("\n--- TENTANDO INTERAGIR COM SELECTS ---")
        
        # Provar com label Servidor
        servidor_label = await page.query_selector('text=Servidor')
        if servidor_label:
            print("Label 'Servidor' encontrado")
            # Pegar o proximo irma
            parent = await servidor_label.evaluate('el => el.parentElement.outerHTML.substring(0, 500)')
            print(f"Parent: {parent[:300]}")

        # Provar com label Franquia
        franquia_label = await page.query_selector('text=Franquia')
        if franquia_label:
            print("Label 'Franquia' encontrado")
            parent = await franquia_label.evaluate('el => el.parentElement.outerHTML.substring(0, 500)')
            print(f"Parent: {parent[:300]}")

        # Tentar achar os selects por aria-label ou outra forma
        all_divs_clickable = await page.query_selector_all('[class*="select"]')
        print(f"\nDivs com 'select' na classe: {len(all_divs_clickable)}")
        for i, div in enumerate(all_divs_clickable[:10]):
            cls = await div.get_attribute('class')
            vis = await div.is_visible()
            text = await div.inner_text()
            if vis:
                print(f"  [{i}] cls='{cls[:60]}' text='{text.strip()[:40]}'")

        # Tentar clicar no primeiro select e ver dropdown
        print("\n--- TENTANDO CLICAR NO SELECT DE SERVIDOR ---")
        try:
            # Achar o primeiro .ant-select-selector e clicar
            first_select = await page.query_selector('.ant-select-selector')
            if first_select:
                await first_select.click()
                await asyncio.sleep(2)
                
                # Ver opcoes do dropdown
                options = await page.query_selector_all('.ant-select-item, .ant-select-dropdown-menu-item, .ant-select-item-option')
                print(f"Opcoes no dropdown: {len(options)}")
                for i, opt in enumerate(options[:15]):
                    text = await opt.inner_text()
                    val = await opt.get_attribute('title') or ''
                    print(f"  option[{i}]: text='{text.strip()[:40]}' title='{val}'")
                
                # Screenshot do dropdown aberto
                await page.screenshot(path="debug_dropdown_servidor.png", full_page=True)
                print("Screenshot dropdown salvo")
        except Exception as e:
            print(f"Erro ao clicar select: {e}")

        await browser.close()
        print("\n--- DIAGNOSTICO V3 COMPLETO ---")

asyncio.run(diagnosticar_v3())
