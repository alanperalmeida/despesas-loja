"""
Diagnostico focado no modal de lojas
Objetivo: encontrar o seletor correto do modal e o checkbox de select all
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

        # ===== FOCO: MODAL DE LOJAS =====
        print("=== INVESTIGANDO BOTAO LOJAS ===")
        
        # O botao de lojas esta no HEADER da pagina, ao lado do dropdown "Loja:"
        # Diferente dos botoes copy dentro do formulario
        # Vamos identificar qual botao e o correto
        
        header_info = await page.evaluate('''() => {
            // Buscar o botao copy no header (proximo ao texto "Loja")
            const allBtns = document.querySelectorAll('button');
            const results = [];
            for (let i = 0; i < allBtns.length; i++) {
                const btn = allBtns[i];
                const icon = btn.querySelector('.anticon-copy');
                if (icon) {
                    // Verifica contexto do botao
                    const parent = btn.closest('.ant-card-head, .ant-layout-header, header, nav, [class*="header"], [class*="toolbar"]');
                    const prevText = btn.previousElementSibling ? btn.previousElementSibling.textContent.trim().substring(0, 30) : 'N/A';
                    const parentText = btn.parentElement ? btn.parentElement.textContent.trim().substring(0, 60) : 'N/A';
                    results.push({
                        index: i,
                        parentClass: btn.parentElement?.className?.substring(0, 80),
                        prevText: prevText,
                        parentText: parentText,
                        inHeader: !!parent,
                        rect: btn.getBoundingClientRect()
                    });
                }
            }
            return results;
        }''')
        print(f"  Botoes copy encontrados: {len(header_info)}")
        for info in header_info:
            print(f"    #{info['index']}: top={info['rect']['top']:.0f}, parent='{info['parentClass']}'")

        # O botao de lojas e o PRIMEIROcopy (no topo, ao lado do dropdown Loja)
        # Vamos clicar nele
        print("\n=== CLICANDO NO BOTAO DE LOJAS (copy no header) ===")
        
        # Usar o botao do header (ao lado do dropdown Loja)
        # Pelo screenshot, o botao esta no topo junto ao "Loja: VIA BRASIL [1000]"
        header_copy = await page.query_selector('button:has(.anticon-copy)')
        if header_copy:
            await header_copy.click()
            await asyncio.sleep(2)
            await ss(page, '20_apos_click_lojas')
            
            # Investigar TODA a estrutura de modais/dialogs na pagina
            modal_analysis = await page.evaluate('''() => {
                const results = {};
                
                // Verificar ant-modal
                results.antModal = document.querySelectorAll('.ant-modal').length;
                results.antModalContent = document.querySelectorAll('.ant-modal-content').length;
                results.antModalWrap = document.querySelectorAll('.ant-modal-wrap').length;
                
                // Verificar dialogs
                results.dialog = document.querySelectorAll('[role="dialog"]').length;
                
                // Verificar drawer
                results.drawer = document.querySelectorAll('.ant-drawer').length;
                results.drawerContent = document.querySelectorAll('.ant-drawer-content').length;
                
                // Verificar overlays genericos
                results.overlay = document.querySelectorAll('.ant-modal-mask').length;
                
                // Verificar tabela dentro de modal/dialog  
                let tables = document.querySelectorAll('table');
                results.totalTables = tables.length;
                
                // Verificar se existe um container "Multiloja" visivel
                const body = document.body.innerHTML;
                results.containsMultiloja = body.includes('Multiloja');
                results.containsFechar = body.includes('Fechar');
                
                // Buscar o container que tem "Multiloja" como title/header
                const allH = document.querySelectorAll('h1,h2,h3,h4,h5,h6,.ant-modal-title,.ant-drawer-title,div');
                let multilojaParent = null;
                for (const h of allH) {
                    if (h.textContent.trim() === 'Multiloja') {
                        multilojaParent = h.closest('.ant-modal, .ant-drawer, .ant-modal-wrap, [role="dialog"]');
                        results.multilojaElementTag = h.tagName;
                        results.multilojaElementClass = h.className;
                        results.multilojaParentTag = multilojaParent?.tagName;
                        results.multilojaParentClass = multilojaParent?.className?.substring(0, 100);
                        break;
                    }
                }
                
                // Se nao achou parent, buscar o wrapper mais proximo
                if (!multilojaParent) {
                    for (const h of allH) {
                        if (h.textContent.trim() === 'Multiloja') {
                            let el = h;
                            for (let i = 0; i < 10; i++) {
                                el = el.parentElement;
                                if (!el) break;
                                results[`parent_${i}`] = {tag: el.tagName, class: el.className?.substring(0, 80)};
                            }
                            break;
                        }
                    }
                }
                
                return results;
            }''')
            print(f"  Modal analysis: {modal_analysis}")
            
            # Agora investigar checkbox do header da tabela dentro do modal
            checkbox_info = await page.evaluate('''() => {
                // Buscar o elemento "Multiloja" e subir ate o container
                const allEl = document.querySelectorAll('*');
                let container = null;
                for (const el of allEl) {
                    if (el.childNodes.length === 1 && el.textContent.trim() === 'Multiloja') {
                        // Subir ate achar algo grande
                        let p = el;
                        while (p.parentElement && p.parentElement.tagName !== 'BODY') {
                            p = p.parentElement;
                            if (p.querySelector('table') && p.querySelector('button')) {
                                container = p;
                                break;
                            }
                        }
                        break;
                    }
                }
                
                if (!container) return {error: 'Container Multiloja nao encontrado'};
                
                const result = {
                    containerTag: container.tagName,
                    containerClass: container.className?.substring(0, 100),
                };
                
                // Dentro do container, buscar checkboxes
                const headerCheckbox = container.querySelector('thead .ant-checkbox-wrapper');
                const headerCheckbox2 = container.querySelector('th .ant-checkbox-wrapper');
                const headerCheckbox3 = container.querySelector('.ant-checkbox-wrapper');
                
                result.headerCheckboxFound = !!headerCheckbox;
                result.thCheckboxFound = !!headerCheckbox2;
                result.anyCheckboxFound = !!headerCheckbox3;
                
                // Buscar o icone "minus" (indeterminado)
                const indeterminate = container.querySelector('.ant-checkbox-indeterminate');
                result.indeterminateFound = !!indeterminate;
                
                // Buscar TODOS os checkboxes na tabela
                const allCheckboxes = container.querySelectorAll('.ant-checkbox-wrapper');
                result.totalCheckboxes = allCheckboxes.length;
                
                // Estado do primeiro checkbox (header)
                if (headerCheckbox || headerCheckbox2) {
                    const hc = headerCheckbox || headerCheckbox2;
                    result.headerCheckboxClasses = hc.className;
                    const inner = hc.querySelector('.ant-checkbox');
                    result.headerInnerClasses = inner ? inner.className : 'N/A';
                }
                
                // Contar checked vs unchecked no tbody
                const tbodyChecked = container.querySelectorAll('tbody .ant-checkbox-wrapper-checked');
                const tbodyAll = container.querySelectorAll('tbody .ant-checkbox-wrapper');
                result.tbodyChecked = tbodyChecked.length;
                result.tbodyTotal = tbodyAll.length;
                
                // HTML do primeiro th com checkbox
                const th = container.querySelector('thead th');
                result.firstThHTML = th ? th.innerHTML.substring(0, 200) : 'N/A';
                
                return result;
            }''')
            print(f"  Checkbox info: {checkbox_info}")
            
            # === AGORA TENTAR CLICAR ===
            if checkbox_info.get('error'):
                print(f"  ERRO: {checkbox_info['error']}")
            else:
                print("\n=== TENTANDO CLICAR NO HEADER CHECKBOX ===")
                
                # Abordagem 1: Click direto no primeiro checkbox do container Multiloja
                click_result = await page.evaluate('''() => {
                    // Encontrar container
                    const allEl = document.querySelectorAll('*');
                    let container = null;
                    for (const el of allEl) {
                        if (el.childNodes.length === 1 && el.textContent.trim() === 'Multiloja') {
                            let p = el;
                            while (p.parentElement && p.parentElement.tagName !== 'BODY') {
                                p = p.parentElement;
                                if (p.querySelector('table') && p.querySelector('button')) {
                                    container = p;
                                    break;
                                }
                            }
                            break;
                        }
                    }
                    if (!container) return 'Container nao encontrado';
                    
                    // Clicar no header checkbox (primeiro th .ant-checkbox-wrapper)
                    const headerChk = container.querySelector('thead .ant-checkbox-wrapper');
                    if (!headerChk) {
                        // Tentar label ou span
                        const headerInput = container.querySelector('thead input[type="checkbox"]');
                        if (headerInput) {
                            headerInput.click();
                            return 'clicked header input';
                        }
                        return 'header checkbox NOT found';
                    }
                    
                    headerChk.click();
                    return 'clicked header wrapper';
                }''')
                print(f"  Click result: {click_result}")
                await asyncio.sleep(1)
                await ss(page, '21_apos_click_header_checkbox')
                
                # Verificar resultado
                post_click = await page.evaluate('''() => {
                    const allEl = document.querySelectorAll('*');
                    let container = null;
                    for (const el of allEl) {
                        if (el.childNodes.length === 1 && el.textContent.trim() === 'Multiloja') {
                            let p = el;
                            while (p.parentElement && p.parentElement.tagName !== 'BODY') {
                                p = p.parentElement;
                                if (p.querySelector('table') && p.querySelector('button')) {
                                    container = p;
                                    break;
                                }
                            }
                            break;
                        }
                    }
                    if (!container) return {error: 'N/A'};
                    
                    const checked = container.querySelectorAll('tbody .ant-checkbox-wrapper-checked');
                    const total = container.querySelectorAll('tbody .ant-checkbox-wrapper');
                    
                    // Buscar texto "Selecionada"
                    const selecionada = container.innerText.match(/Selecionada:\\s*(\\d+)/);
                    
                    return {
                        checked: checked.length,
                        total: total.length,
                        selecionadaText: selecionada ? selecionada[0] : 'nao encontrado',
                    };
                }''')
                print(f"  Apos click: {post_click}")
                
                # Se ainda nao selecionou todos, clicar 2 vezes (toggle)
                if post_click.get('checked', 0) < post_click.get('total', 16):
                    print("  Primeira tentativa nao selecionou todos. Clicando novamente...")
                    await page.evaluate('''() => {
                        const allEl = document.querySelectorAll('*');
                        let container = null;
                        for (const el of allEl) {
                            if (el.childNodes.length === 1 && el.textContent.trim() === 'Multiloja') {
                                let p = el;
                                while (p.parentElement && p.parentElement.tagName !== 'BODY') {
                                    p = p.parentElement;
                                    if (p.querySelector('table') && p.querySelector('button')) {
                                        container = p;
                                        break;
                                    }
                                }
                                break;
                            }
                        }
                        if (!container) return;
                        const headerChk = container.querySelector('thead .ant-checkbox-wrapper');
                        if (headerChk) headerChk.click();
                    }''')
                    await asyncio.sleep(1)
                    
                    post_click2 = await page.evaluate('''() => {
                        const allEl = document.querySelectorAll('*');
                        let container = null;
                        for (const el of allEl) {
                            if (el.childNodes.length === 1 && el.textContent.trim() === 'Multiloja') {
                                let p = el;
                                while (p.parentElement && p.parentElement.tagName !== 'BODY') {
                                    p = p.parentElement;
                                    if (p.querySelector('table') && p.querySelector('button')) {
                                        container = p;
                                        break;
                                    }
                                }
                                break;
                            }
                        }
                        if (!container) return {error: 'N/A'};
                        const checked = container.querySelectorAll('tbody .ant-checkbox-wrapper-checked');
                        const total = container.querySelectorAll('tbody .ant-checkbox-wrapper');
                        return {checked: checked.length, total: total.length};
                    }''')
                    print(f"  Apos segundo click: {post_click2}")
                    await ss(page, '22_apos_segundo_click')
                    
                    # Se AINDA nao selecionou, tentar individual
                    if post_click2.get('checked', 0) < post_click2.get('total', 16):
                        print("  Ainda parcial! Tentando marcar individualmente...")
                        individual = await page.evaluate('''() => {
                            const allEl = document.querySelectorAll('*');
                            let container = null;
                            for (const el of allEl) {
                                if (el.childNodes.length === 1 && el.textContent.trim() === 'Multiloja') {
                                    let p = el;
                                    while (p.parentElement && p.parentElement.tagName !== 'BODY') {
                                        p = p.parentElement;
                                        if (p.querySelector('table') && p.querySelector('button')) {
                                            container = p;
                                            break;
                                        }
                                    }
                                    break;
                                }
                            }
                            if (!container) return 'N/A';
                            
                            const unchecked = container.querySelectorAll('tbody .ant-checkbox-wrapper:not(.ant-checkbox-wrapper-checked)');
                            let clicked = 0;
                            for (const chk of unchecked) {
                                chk.click();
                                clicked++;
                            }
                            return {clickedIndividual: clicked};
                        }''')
                        print(f"  Individual: {individual}")
                        await asyncio.sleep(1)
                        await ss(page, '23_apos_individual')
                        
                        final_count = await page.evaluate('''() => {
                            const allEl = document.querySelectorAll('*');
                            let container = null;
                            for (const el of allEl) {
                                if (el.childNodes.length === 1 && el.textContent.trim() === 'Multiloja') {
                                    let p = el;
                                    while (p.parentElement && p.parentElement.tagName !== 'BODY') {
                                        p = p.parentElement;
                                        if (p.querySelector('table') && p.querySelector('button')) {
                                            container = p;
                                            break;
                                        }
                                    }
                                    break;
                                }
                            }
                            if (!container) return {error: 'Nao achou'};
                            const checked = container.querySelectorAll('tbody .ant-checkbox-wrapper-checked');
                            const total = container.querySelectorAll('tbody .ant-checkbox-wrapper');
                            return {checked: checked.length, total: total.length};
                        }''')
                        print(f"  ESTADO FINAL: {final_count}")
            
        else:
            print("  Botao de lojas NAO encontrado!")

        print("\n=== FIM DIAGNOSTICO LOJAS ===")
        await browser.close()

if __name__ == '__main__':
    asyncio.run(run())
