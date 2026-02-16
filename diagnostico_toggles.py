"""
Diagnostico rapido: listar TODOS os toggles/switches na pagina de relatorio
"""
import asyncio
from playwright.async_api import async_playwright

CPF = '14549094710'
SENHA = '161097'

import os
os.makedirs('diagnostico_screenshots', exist_ok=True)

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

        # Screenshot da pagina completa
        await page.screenshot(path='diagnostico_screenshots/40_pagina_relatorio_completa.png', full_page=True)

        # Listar TODOS os switches/toggles
        toggles = await page.evaluate('''() => {
            const results = [];
            
            // Buscar todos .ant-switch
            const switches = document.querySelectorAll('.ant-switch');
            for (let i = 0; i < switches.length; i++) {
                const sw = switches[i];
                const isChecked = sw.classList.contains('ant-switch-checked');
                
                // Buscar texto proximo (label, span, div anterior)
                const parent = sw.parentElement;
                let label = 'N/A';
                
                // Tentar texto do irmao anterior
                const prev = sw.previousElementSibling;
                if (prev) label = prev.textContent.trim().substring(0, 50);
                
                // Se nao achou, tentar o pai
                if (label === 'N/A' || label === '') {
                    label = parent ? parent.textContent.trim().substring(0, 80) : 'N/A';
                }
                
                // Posicao na tela
                const rect = sw.getBoundingClientRect();
                
                results.push({
                    index: i,
                    label: label,
                    isChecked: isChecked,
                    top: Math.round(rect.top),
                    left: Math.round(rect.left),
                    parentTag: parent ? parent.tagName : 'N/A',
                    classes: sw.className.substring(0, 100)
                });
            }
            
            // Buscar tambem labels que contenham "Agrupar"
            const allEls = document.querySelectorAll('label, span, div');
            const agruparEls = [];
            for (const el of allEls) {
                const text = el.textContent.trim();
                if (text.toLowerCase().includes('agrupar') && text.length < 50) {
                    agruparEls.push({
                        tag: el.tagName,
                        text: text,
                        class: el.className?.substring(0, 50) || ''
                    });
                }
            }
            
            return {switches: results, agruparElements: agruparEls};
        }''')
        
        print("=== SWITCHES/TOGGLES NA PAGINA ===")
        for sw in toggles['switches']:
            status = "ATIVO" if sw['isChecked'] else "desligado"
            print(f"  #{sw['index']}: [{status}] label='{sw['label']}' (top={sw['top']}, left={sw['left']})")
        
        print(f"\n=== ELEMENTOS COM 'AGRUPAR' ===")
        for el in toggles['agruparElements']:
            print(f"  <{el['tag']}> '{el['text']}' class='{el['class']}'")

        print("\n=== FIM ===")
        await browser.close()

if __name__ == '__main__':
    asyncio.run(run())
