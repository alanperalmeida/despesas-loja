"""
Script de diagnostico para capturar a estrutura HTML das paginas do Degustone.
Salva screenshots e HTML para analise dos seletores corretos.
"""
import asyncio
from playwright.async_api import async_playwright

BASE_URL = "https://degustone.com.br"

async def diagnosticar():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(30000)

        # === PAGINA DE LOGIN ===
        print("--- PAGINA DE LOGIN ---")
        await page.goto(f"{BASE_URL}/login")
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)

        # Screenshot
        await page.screenshot(path="debug_login.png", full_page=True)
        print("Screenshot salvo: debug_login.png")

        # Salvar HTML completo
        html = await page.content()
        with open("debug_login.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("HTML salvo: debug_login.html")

        # Listar todos os inputs
        inputs = await page.query_selector_all('input')
        print(f"\nEncontrados {len(inputs)} campos input:")
        for i, inp in enumerate(inputs):
            tag = await inp.evaluate('el => el.outerHTML')
            print(f"  [{i}] {tag[:200]}")

        # Listar todos os buttons
        buttons = await page.query_selector_all('button, input[type="submit"], a.btn')
        print(f"\nEncontrados {len(buttons)} botoes:")
        for i, btn in enumerate(buttons):
            tag = await btn.evaluate('el => el.outerHTML')
            print(f"  [{i}] {tag[:200]}")

        # Listar todos os forms
        forms = await page.query_selector_all('form')
        print(f"\nEncontrados {len(forms)} formularios:")
        for i, form in enumerate(forms):
            action = await form.get_attribute('action') or '(sem action)'
            method = await form.get_attribute('method') or '(sem method)'
            print(f"  [{i}] action={action} method={method}")

        # Listar todos os selects
        selects = await page.query_selector_all('select')
        print(f"\nEncontrados {len(selects)} selects:")
        for i, sel in enumerate(selects):
            tag = await sel.evaluate('el => el.outerHTML')
            print(f"  [{i}] {tag[:200]}")

        # Listar iframes (caso o formulario esteja em um iframe)
        iframes = await page.query_selector_all('iframe')
        print(f"\nEncontrados {len(iframes)} iframes:")
        for i, iframe in enumerate(iframes):
            src = await iframe.get_attribute('src') or '(sem src)'
            print(f"  [{i}] src={src[:200]}")

        # Tentar achar o campo de CPF e preencher
        print("\n--- TENTANDO PREENCHER CPF ---")
        try:
            await page.fill('input[type="text"]', '14549094710', timeout=5000)
            print("CPF preenchido com sucesso")
            
            # Esperar um pouco para ver se aparece campo de senha
            await asyncio.sleep(3)
            
            # Screenshot apos preencher CPF
            await page.screenshot(path="debug_after_cpf.png", full_page=True)
            print("Screenshot apos CPF salvo: debug_after_cpf.png")
            
            # Salvar HTML apos preencher CPF
            html2 = await page.content()
            with open("debug_after_cpf.html", "w", encoding="utf-8") as f:
                f.write(html2)
            print("HTML apos CPF salvo: debug_after_cpf.html")
            
            # Listar inputs novamente (pode ter mudado)
            inputs2 = await page.query_selector_all('input')
            print(f"\nInputs apos CPF ({len(inputs2)}):")
            for i, inp in enumerate(inputs2):
                tag = await inp.evaluate('el => el.outerHTML')
                print(f"  [{i}] {tag[:200]}")

            # Tentar botao de proximo/avancar
            print("\n--- TENTANDO CLICAR PROXIMO ---")
            buttons2 = await page.query_selector_all('button, input[type="submit"], a.btn, [type="button"]')
            for i, btn in enumerate(buttons2):
                tag = await btn.evaluate('el => el.outerHTML')
                text = await btn.inner_text() if await btn.is_visible() else "(oculto)"
                print(f"  [{i}] text='{text}' -> {tag[:200]}")
                
        except Exception as e:
            print(f"Erro ao preencher CPF: {e}")

        await browser.close()
        print("\n--- DIAGNOSTICO COMPLETO ---")

asyncio.run(diagnosticar())
