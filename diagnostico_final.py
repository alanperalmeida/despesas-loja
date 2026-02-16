"""
Diagnostico FINAL - Estrutura HTML do Drawer + Correcao de next-month-btn
"""
import asyncio
from playwright.async_api import async_playwright

CPF = '14549094710'
SENHA = '161097'

import os
os.makedirs('diagnostico_screenshots', exist_ok=True)

async def ss(page, name):
    path = f'diagnostico_screenshots/{name}.png'
    await page.screenshot(path=path, full_page=False)
    print(f"  >> Screenshot: {path}")

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={'width': 1280, 'height': 900})
        page = await ctx.new_page()
        page.set_default_timeout(30000)

        # LOGIN
        await page.goto('https://degustone.com.br/login')
        await page.wait_for_load_state('networkidle')
        await page.fill('input[name="username"]', CPF)
        btns = await page.query_selector_all('button.ant-btn')
        dm = {}
        for b in btns:
            t = (await b.inner_text()).strip()
            if ' ou ' in t:
                for part in t.split(' ou '):
                    if part.strip().isdigit(): dm[part.strip()] = b
        for d in SENHA: await dm[d].click(); await asyncio.sleep(0.2)
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)

        # FRANQUIA
        combos = await page.query_selector_all('[role="combobox"]')
        await combos[0].click(); await asyncio.sleep(0.5)
        await page.click('.multiselect__element'); await asyncio.sleep(1)
        combos = await page.query_selector_all('[role="combobox"]')
        await combos[1].click(); await asyncio.sleep(0.5)
        opts = await page.query_selector_all('.multiselect__element')
        for o in opts:
            if 'OFFICE' in (await o.inner_text()).upper():
                await o.click(); break
        await asyncio.sleep(1)
        await page.click('button:has-text("Prosseguir")')
        await asyncio.sleep(5)

        # NAVEGAR
        try: await page.click('.fa-xmark', timeout=2000)
        except: pass
        await page.evaluate('() => window.$nuxt.$router.push("/relatorio/despesas-loja")')
        await asyncio.sleep(5)
        try: await page.click('.fa-xmark', timeout=2000)
        except: pass

        # =========================================================
        # PARTE 1: ESTRUTURA DO DRAWER
        # =========================================================
        print("=" * 60)
        print("PARTE 1: ESTRUTURA DO DRAWER MULTILOJA")
        print("=" * 60)
        
        copy_btn = await page.query_selector('button:has(.anticon-copy)')
        await copy_btn.click()
        await asyncio.sleep(2)
        
        drawer = await page.query_selector('.ant-drawer.ant-drawer-open')
        if drawer:
            await ss(page, '30_drawer_aberto')
            
            # Capturar HTML do conteudo do drawer (primeiros 3000 chars)
            drawer_html = await drawer.evaluate('el => el.innerHTML.substring(0, 3000)')
            print(f"\n  DRAWER HTML (primeiros 3000 chars):\n{drawer_html}\n")
            
            # Verificar especificamente o que existe dentro do drawer
            drawer_analysis = await drawer.evaluate('''el => {
                const result = {};
                
                // Tabelas
                result.tables = el.querySelectorAll('table').length;
                result.antTable = el.querySelectorAll('.ant-table').length;
                result.antTableWrapper = el.querySelectorAll('.ant-table-wrapper').length;
                
                // Headers
                result.thead = el.querySelectorAll('thead').length;
                result.th = el.querySelectorAll('th').length;
                
                // Body
                result.tbody = el.querySelectorAll('tbody').length;
                result.tbodyTr = el.querySelectorAll('tbody tr').length;
                
                // Checkboxes - varias classes possiveis
                result.checkboxWrapper = el.querySelectorAll('.ant-checkbox-wrapper').length;
                result.checkbox = el.querySelectorAll('.ant-checkbox').length;
                result.checkboxInput = el.querySelectorAll('input[type="checkbox"]').length;
                result.checkboxChecked = el.querySelectorAll('.ant-checkbox-checked').length;
                result.checkboxWrapperChecked = el.querySelectorAll('.ant-checkbox-wrapper-checked').length;
                
                // Dentro da drawer-content ou drawer-body
                result.drawerBody = el.querySelectorAll('.ant-drawer-body').length;
                result.drawerContent = el.querySelectorAll('.ant-drawer-content').length;
                
                // Linhas com texto (para confirmar as lojas)
                const trs = el.querySelectorAll('tbody tr');
                if (trs.length > 0) {
                    result.firstRowText = trs[0].innerText.trim().substring(0, 100);
                }
                
                // Verificar se o checkbox esta dentro de ant-table-selection
                result.selectionColumn = el.querySelectorAll('.ant-table-selection-column').length;
                result.selectionCell = el.querySelectorAll('.ant-table-selection').length;
                
                return result;
            }''')
            print(f"  DRAWER ANALYSIS: {drawer_analysis}")
            
            # Se tem checkboxes, vamos tentar clicar
            if drawer_analysis['checkboxWrapper'] > 0:
                print(f"\n  Encontrados {drawer_analysis['checkboxWrapper']} checkboxes!")
                
                # Buscar o checkbox do header via .ant-table-selection
                header_sel = await drawer.query_selector('.ant-table-selection .ant-checkbox-wrapper')
                if not header_sel:
                    header_sel = await drawer.query_selector('thead .ant-checkbox-wrapper')
                if not header_sel:
                    header_sel = await drawer.query_selector('th .ant-checkbox-wrapper')
                
                if header_sel:
                    print("  Encontrado header checkbox! Clicando...")
                    # Verificar se indeterminado
                    cls = await header_sel.evaluate('el => el.innerHTML')
                    print(f"  Header checkbox inner HTML: {cls[:200]}")
                    
                    await header_sel.click(force=True)
                    await asyncio.sleep(1)
                    
                    # Verificar
                    post = await drawer.evaluate('''el => ({
                        checked: el.querySelectorAll('.ant-checkbox-wrapper-checked').length,
                        total: el.querySelectorAll('tbody .ant-checkbox-wrapper').length,
                        indeterminate: el.querySelectorAll('.ant-checkbox-indeterminate').length
                    })''')
                    print(f"  Apos 1o click: {post}")
                    
                    # Se indeterminado, clicar novamente
                    if post.get('indeterminate', 0) > 0 or post['checked'] < post['total']:
                        print("  Clicando novamente (indeterminado->todos)...")
                        await header_sel.click(force=True)
                        await asyncio.sleep(1)
                        post2 = await drawer.evaluate('''el => ({
                            checked: el.querySelectorAll('.ant-checkbox-wrapper-checked').length,
                            total: el.querySelectorAll('tbody .ant-checkbox-wrapper').length,
                        })''')
                        print(f"  Apos 2o click: {post2}")
                        
                        # Se AINDA nao marcou todos, clicar um por um via JS
                        if post2['checked'] < post2['total']:
                            print("  Ainda parcial! Clicando via JS...")
                            await drawer.evaluate('''el => {
                                const unchecked = el.querySelectorAll('tbody .ant-checkbox-wrapper:not(.ant-checkbox-wrapper-checked)');
                                unchecked.forEach(chk => chk.click());
                            }''')
                            await asyncio.sleep(1)
                    
                    await ss(page, '31_lojas_selecionadas')
                    
                    # Contagem final
                    final = await drawer.evaluate('''el => ({
                        checked: el.querySelectorAll('.ant-checkbox-wrapper-checked').length,
                        total: el.querySelectorAll('tbody .ant-checkbox-wrapper').length,
                    })''')
                    print(f"\n  RESULTADO FINAL LOJAS: {final['checked']}/{final['total']}")
                    
                else:
                    print("  NENHUM header checkbox encontrado! Tentando via JS generico...")
                    # Forcar click em todos os checkboxes nao marcados
                    await drawer.evaluate('''el => {
                        const cbs = el.querySelectorAll('.ant-checkbox-wrapper:not(.ant-checkbox-wrapper-checked)');
                        cbs.forEach(cb => cb.click());
                    }''')
                    await asyncio.sleep(1)
                    post = await drawer.evaluate('''el => ({
                        checked: el.querySelectorAll('.ant-checkbox-wrapper-checked').length,
                        total: el.querySelectorAll('.ant-checkbox-wrapper').length,
                    })''')
                    print(f"  Apos click forçado: {post}")
            else:
                print("  NENHUM checkbox encontrado no drawer!")
            
            # Fechar drawer
            try: 
                close = await drawer.query_selector('button:has-text("Fechar")')
                if close: await close.click()
                else: await page.keyboard.press('Escape')
            except: await page.keyboard.press('Escape')
            await asyncio.sleep(1)
        else:
            print("  Drawer NAO encontrado!")
        
        # =========================================================
        # PARTE 2: TESTE NEXT-MONTH COM RE-QUERY
        # =========================================================
        print("\n" + "=" * 60)
        print("PARTE 2: NAVEGACAO DE MESES COM RE-QUERY DO BOTAO")  
        print("=" * 60)
        
        picker = await page.query_selector('.ant-calendar-picker')
        if picker:
            await picker.click(force=True)
            await asyncio.sleep(1)
            
            # Voltar para jan 2025
            prev_year = await page.query_selector('.ant-calendar-prev-year-btn')
            if prev_year: await prev_year.click(); await asyncio.sleep(0.3)
            
            # Clicar dia 1
            await page.evaluate('''() => {
                const tds = document.querySelectorAll('td.ant-calendar-cell:not(.ant-calendar-last-month-cell):not(.ant-calendar-next-month-cell)');
                for (const td of tds) {
                    if (td.innerText.trim() === '1') { td.click(); return; }
                }
            }''')
            await asyncio.sleep(1)
            
            # Navegar 14 meses com RE-QUERY do botao a cada clique
            print("  Navegando 14 meses com re-query...")
            for i in range(14):
                # RE-QUERY do botao a cada iteracao (evita stale element)
                next_btn = await page.query_selector('.ant-calendar-next-month-btn')
                if next_btn:
                    await next_btn.click()
                    await asyncio.sleep(0.3)
                else:
                    print(f"  ERRO: next-month-btn perdido na iteracao {i}!")
                    break
                    
                if i % 3 == 0:
                    info = await page.evaluate('''() => ({
                        y: document.querySelector('.ant-calendar-year-select')?.innerText,
                        m: document.querySelector('.ant-calendar-month-select')?.innerText
                    })''')
                    print(f"    Iteracao {i}: {info}")
            
            # Verificar destino final
            final_info = await page.evaluate('''() => ({
                y: document.querySelector('.ant-calendar-year-select')?.innerText,
                m: document.querySelector('.ant-calendar-month-select')?.innerText
            })''')
            print(f"  Destino final apos 14 cliques: {final_info}")
            
            # Clicar dia 31
            clicked = await page.evaluate('''() => {
                const tds = document.querySelectorAll('td.ant-calendar-cell:not(.ant-calendar-last-month-cell):not(.ant-calendar-next-month-cell)');
                for (const td of tds) {
                    if (td.innerText.trim() === '31') { td.click(); return 'clicked 31'; }
                }
                return 'day 31 not found';
            }''')
            print(f"  Click dia 31: {clicked}")
            await asyncio.sleep(1)
            
            # Verificar inputs finais
            dates = await page.evaluate('''() => {
                const inputs = document.querySelectorAll('.ant-calendar-range-picker-input');
                return Array.from(inputs).map(i => i.value);
            }''')
            print(f"  DATAS FINAIS: {dates}")
            await ss(page, '32_datas_finais')
        
        print("\n=== FIM DIAGNOSTICO FINAL ===")
        await browser.close()

if __name__ == '__main__':
    asyncio.run(run())
