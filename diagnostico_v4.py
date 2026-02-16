"""
Diagnostico v4: Apos selecionar franquia e clicar Prosseguir,
investigar a pagina principal para encontrar menu de navegacao
"""
import asyncio
from playwright.async_api import async_playwright

CPF = '14549094710'
SENHA = '161097'
BASE_URL = 'https://degustone.com.br'

async def login(page):
    await page.goto(f"{BASE_URL}/login")
    await page.wait_for_load_state('networkidle')
    await asyncio.sleep(2)
    await page.fill('input[name="username"]', CPF)
    buttons = await page.query_selector_all(
        'button.ant-btn.ant-btn-primary.ant-btn-lg:not(.btn-backspace)')
    digit_map = {}
    for btn in buttons:
        text = (await btn.inner_text()).strip()
        if ' ou ' in text:
            for part in text.split(' ou '):
                d = part.strip()
                if d.isdigit():
                    digit_map[d] = btn
    for d in SENHA:
        await digit_map[d].click()
        await asyncio.sleep(0.2)
    await page.click('button[type="submit"]')
    await page.wait_for_load_state('networkidle')
    await asyncio.sleep(5)
    print(f"Login OK: {page.url}")

async def selecionar_franquia(page):
    await page.wait_for_selector('[role="combobox"]', timeout=15000)
    await asyncio.sleep(2)
    comboboxes = await page.query_selector_all('[role="combobox"]')
    
    # Servidor
    await comboboxes[0].click()
    await asyncio.sleep(1)
    opts = await page.query_selector_all('.multiselect__element')
    if opts:
        await opts[0].click()
    await asyncio.sleep(2)
    
    # Franquia
    comboboxes = await page.query_selector_all('[role="combobox"]')
    await comboboxes[1].click()
    await asyncio.sleep(1)
    opts = await page.query_selector_all('.multiselect__element')
    for opt in opts:
        text = (await opt.inner_text()).strip()
        if 'OFFICE' in text.upper():
            await opt.click()
            print(f"Franquia selecionada: {text}")
            break
    await asyncio.sleep(1)
    
    # Prosseguir
    await page.click('button:has-text("Prosseguir")')
    await page.wait_for_load_state('networkidle')
    await asyncio.sleep(5)
    print(f"Apos Prosseguir: {page.url}")

async def diagnosticar_v4():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(30000)

        await login(page)
        await selecionar_franquia(page)

        # ====== PAGINA PRINCIPAL (DASHBOARD) ======
        print("\n=== PAGINA PRINCIPAL APOS SELECAO ===")
        print(f"URL: {page.url}")
        
        # Screenshot
        await page.screenshot(path="debug_v4_dashboard.png", full_page=True)
        print("Screenshot: debug_v4_dashboard.png")

        # Procurar menus de navegacao
        print("\n--- MENUS ---")
        menus = await page.query_selector_all('.ant-menu, .ant-menu-item, nav, [class*="sidebar"], [class*="nav"]')
        print(f"Menu elements: {len(menus)}")
        for i, m in enumerate(menus[:15]):
            text = await m.inner_text()
            cls = await m.get_attribute('class') or ''
            vis = await m.is_visible()
            if vis and text.strip():
                print(f"  [{i}] cls='{cls[:60]}' text='{text.strip()[:80]}'")

        # Procurar links
        print("\n--- LINKS ---")
        links = await page.query_selector_all('a')
        for i, link in enumerate(links):
            text = (await link.inner_text()).strip()
            href = await link.get_attribute('href') or ''
            vis = await link.is_visible()
            if vis and text:
                print(f"  [{i}] text='{text[:50]}' href='{href[:60]}'")

        # Procurar todos botoes
        print("\n--- BOTOES ---")
        btns = await page.query_selector_all('button')
        for i, btn in enumerate(btns):
            text = (await btn.inner_text()).strip()
            vis = await btn.is_visible()
            if vis and text:
                print(f"  [{i}] text='{text[:50]}'")

        # Ant Layout?
        print("\n--- LAYOUT ---")
        layouts = await page.query_selector_all('.ant-layout, .ant-layout-header, .ant-layout-sider, .ant-layout-content')
        print(f"Layout elements: {len(layouts)}")
        for i, l in enumerate(layouts):
            cls = await l.get_attribute('class') or ''
            vis = await l.is_visible()
            print(f"  [{i}] cls='{cls[:60]}' visible={vis}")

        # Body text abreviado
        print("\n--- BODY TEXT (primeiros 500 chars) ---")
        body_text = await page.inner_text('body')
        print(body_text[:500])

        # Interceptar requisicoes ao navegar
        print("\n--- TESTANDO NAVEGACAO POR JS ---")
        # Tentar usar o router Vue diretamente
        try:
            result = await page.evaluate('() => { try { return JSON.stringify(window.$nuxt.$route); } catch(e) { return "Nuxt nao disponivel: "+e.message; } }')
            print(f"Nuxt route: {result}")
        except Exception as e:
            print(f"Erro ao acessar Nuxt: {e}")

        # Tentar navegar via Nuxt router
        try:
            await page.evaluate('() => { window.$nuxt.$router.push("/relatorio/despesas-loja"); }')
            await asyncio.sleep(5)
            print(f"Apos navegacao via Nuxt: {page.url}")
            
            # Screenshot
            await page.screenshot(path="debug_v4_relatorio.png", full_page=True)
            print("Screenshot: debug_v4_relatorio.png")

            # Ver tabelas
            tbodies = await page.query_selector_all('tbody')
            theads = await page.query_selector_all('thead')
            print(f"\nTabelas no relatorio: thead={len(theads)}, tbody={len(tbodies)}")
            for i, thead in enumerate(theads[:3]):
                ths = await thead.query_selector_all('th')
                texts = []
                for th in ths:
                    t = await th.inner_text()
                    texts.append(t.strip()[:20])
                print(f"  thead[{i}]: {texts}")
            
            for i, tbody in enumerate(tbodies[:3]):
                trs = await tbody.query_selector_all('tr')
                print(f"  tbody[{i}]: {len(trs)} linhas")
                for j, tr in enumerate(trs[:3]):
                    tds = await tr.query_selector_all('td')
                    texts = []
                    for td in tds:
                        t = await td.inner_text()
                        texts.append(t.strip()[:25])
                    print(f"    tr[{j}]: {texts[:6]}")

        except Exception as e:
            print(f"Erro ao navegar via Nuxt router: {e}")

        await browser.close()
        print("\n=== DIAGNOSTICO V4 COMPLETO ===")

asyncio.run(diagnosticar_v4())
