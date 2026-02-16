"""
Diagnostico Visual Completo - Screenshot a cada passo
Objetivo: VER exatamente o que acontece na tela em cada interacao
"""
import asyncio
from playwright.async_api import async_playwright

CPF = '14549094710'
SENHA = '161097'
SCREENSHOT_DIR = 'diagnostico_screenshots'

import os
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

async def ss(page, name):
    path = f'{SCREENSHOT_DIR}/{name}.png'
    await page.screenshot(path=path, full_page=False)
    print(f"  >> Screenshot: {path}")

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={'width': 1280, 'height': 900})
        page = await ctx.new_page()
        page.set_default_timeout(30000)

        # === LOGIN ===
        print("=== 1. LOGIN ===")
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
        print(f"  URL apos login: {page.url}")

        # === SELECAO FRANQUIA ===
        print("\n=== 2. SELECAO FRANQUIA ===")
        await page.wait_for_selector('[role="combobox"]')
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

        # === NAVEGAR RELATORIO ===
        print("\n=== 3. NAVEGAR RELATORIO ===")
        try: await page.click('.fa-xmark', timeout=2000)
        except: pass
        await page.evaluate('() => window.$nuxt.$router.push("/relatorio/despesas-loja")')
        await asyncio.sleep(5)
        try: await page.click('.fa-xmark', timeout=2000)
        except: pass

        await ss(page, '01_pagina_relatorio')
        print(f"  URL: {page.url}")

        # === TESTE CALENDARIO ===
        print("\n=== 4. CALENDARIO - Estado Inicial ===")
        
        # Verificar se o picker existe e qual o estado
        picker = await page.query_selector('.ant-calendar-picker')
        if not picker:
            print("  ERRO: .ant-calendar-picker NAO encontrado!")
            # Tentar outro seletor
            picker = await page.query_selector('.ant-calendar-picker-input')
            if picker:
                print("  Encontrado .ant-calendar-picker-input")
        
        # Ler o valor atual dos inputs de data
        current_dates = await page.evaluate('''() => {
            const inputs = document.querySelectorAll('.ant-calendar-range-picker-input');
            return Array.from(inputs).map(i => i.value || i.placeholder || i.innerText || 'VAZIO');
        }''')
        print(f"  Datas atuais nos inputs: {current_dates}")
        
        await ss(page, '02_antes_abrir_calendario')

        # Abrir calendario
        print("\n=== 5. ABRINDO CALENDARIO ===")
        if picker:
            await picker.click(force=True)
            await asyncio.sleep(1)
            await ss(page, '03_calendario_aberto')
            
            # Ler header do calendario (ano e mes)
            cal_info = await page.evaluate('''() => {
                const yearEl = document.querySelector('.ant-calendar-year-select');
                const monthEl = document.querySelector('.ant-calendar-month-select');
                const prevYearBtn = document.querySelector('.ant-calendar-prev-year-btn');
                const prevMonthBtn = document.querySelector('.ant-calendar-prev-month-btn');
                const nextMonthBtn = document.querySelector('.ant-calendar-next-month-btn');
                const nextYearBtn = document.querySelector('.ant-calendar-next-year-btn');
                return {
                    year: yearEl ? yearEl.innerText : 'NAO ENCONTRADO',
                    month: monthEl ? monthEl.innerText : 'NAO ENCONTRADO', 
                    prevYearExists: !!prevYearBtn,
                    prevMonthExists: !!prevMonthBtn,
                    nextMonthExists: !!nextMonthBtn,
                    nextYearExists: !!nextYearBtn,
                    // Verificar se sao visiveis
                    prevYearVisible: prevYearBtn ? window.getComputedStyle(prevYearBtn).display !== 'none' : false,
                    prevMonthVisible: prevMonthBtn ? window.getComputedStyle(prevMonthBtn).display !== 'none' : false,
                };
            }''')
            print(f"  Ano: {cal_info['year']}, Mes: {cal_info['month']}")
            print(f"  Botao << (PrevYear): existe={cal_info['prevYearExists']}, visivel={cal_info['prevYearVisible']}")
            print(f"  Botao < (PrevMonth): existe={cal_info['prevMonthExists']}, visivel={cal_info['prevMonthVisible']}")

            # === CLICAR << (Prev Year) ===
            print("\n=== 6. CLICANDO << (Ano Anterior) ===")
            prev_year = await page.query_selector('.ant-calendar-prev-year-btn')
            if prev_year:
                await prev_year.click()
                await asyncio.sleep(0.5)
                await ss(page, '04_apos_prev_year')
                new_year = await page.evaluate("document.querySelector('.ant-calendar-year-select')?.innerText || 'N/A'")
                print(f"  Ano apos <<: {new_year}")
            else:
                print("  ERRO: Botao << NAO encontrado!")

            # === CLICAR < (Prev Month) ===
            print("\n=== 7. CLICANDO < (Mes Anterior) ===")
            # Verificar mes atual
            curr_month = await page.evaluate("document.querySelector('.ant-calendar-month-select')?.innerText || 'N/A'")
            print(f"  Mes atual: {curr_month}")
            
            prev_month = await page.query_selector('.ant-calendar-prev-month-btn')
            if prev_month:
                await prev_month.click()
                await asyncio.sleep(0.5)
                await ss(page, '05_apos_prev_month')
                new_month = await page.evaluate("document.querySelector('.ant-calendar-month-select')?.innerText || 'N/A'")
                print(f"  Mes apos <: {new_month}")
            else:
                print("  ERRO: Botao < NAO encontrado!")

            # === CLICAR DIA 1 ===
            print("\n=== 8. CLICANDO DIA 1 ===")
            # Listar dias disponiveis
            days_info = await page.evaluate('''() => {
                const tds = document.querySelectorAll('.ant-calendar-range-part td.ant-calendar-cell');
                const result = [];
                for (const td of tds) {
                    const dateEl = td.querySelector('.ant-calendar-date');
                    if (dateEl) {
                        result.push({
                            day: dateEl.innerText.trim(),
                            isLastMonth: td.classList.contains('ant-calendar-last-month-cell'),
                            isNextMonth: td.classList.contains('ant-calendar-next-month-cell'),
                            isSelected: td.classList.contains('ant-calendar-selected-day'),
                            classes: td.className
                        });
                    }
                }
                return result.slice(0, 10); // Primeiros 10
            }''')
            print(f"  Primeiros dias visíveis: {days_info}")
            
            # Clicar no dia 1
            clicked = await page.evaluate('''() => {
                const tds = document.querySelectorAll('td.ant-calendar-cell');
                for (const td of tds) {
                    if (!td.classList.contains('ant-calendar-last-month-cell') && 
                        !td.classList.contains('ant-calendar-next-month-cell')) {
                        const dateEl = td.querySelector('.ant-calendar-date');
                        if (dateEl && dateEl.innerText.trim() === '1') {
                            dateEl.click();
                            return 'clicked day 1';
                        }
                    }
                }
                return 'day 1 NOT found';
            }''')
            print(f"  Resultado: {clicked}")
            await asyncio.sleep(1)
            await ss(page, '06_apos_click_dia1')

            # Verificar se calendario ainda aberto e navegar > para proximo mes
            print("\n=== 9. NAVEGANDO > PARA MES SEGUINTE ===")
            next_month = await page.query_selector('.ant-calendar-next-month-btn')
            if next_month:
                await next_month.click()
                await asyncio.sleep(0.5)
                await ss(page, '07_apos_next_month')
                info2 = await page.evaluate('''() => ({
                    year: document.querySelector('.ant-calendar-year-select')?.innerText,
                    month: document.querySelector('.ant-calendar-month-select')?.innerText
                })''')
                print(f"  Calendario agora: {info2}")
            
            # Clicar dia 28 (ultimo dia de fev)
            print("\n=== 10. CLICANDO DIA 28 ===")
            clicked2 = await page.evaluate('''() => {
                const tds = document.querySelectorAll('td.ant-calendar-cell');
                for (const td of tds) {
                    if (!td.classList.contains('ant-calendar-last-month-cell') && 
                        !td.classList.contains('ant-calendar-next-month-cell')) {
                        const dateEl = td.querySelector('.ant-calendar-date');
                        if (dateEl && dateEl.innerText.trim() === '28') {
                            dateEl.click();
                            return 'clicked day 28';
                        }
                    }
                }
                return 'day 28 NOT found';
            }''')
            print(f"  Resultado: {clicked2}")
            await asyncio.sleep(1)
            await ss(page, '08_apos_click_dia28')

            # Verificar os valores dos inputs apos range
            final_dates = await page.evaluate('''() => {
                const inputs = document.querySelectorAll('.ant-calendar-range-picker-input');
                return Array.from(inputs).map(i => i.value || 'VAZIO');
            }''')
            print(f"  Datas finais nos inputs: {final_dates}")

        # === TESTE LOJAS ===
        print("\n=== 11. TESTE LOJAS ===")
        await ss(page, '09_antes_lojas')
        
        # Encontrar botao de lojas
        copy_btns = await page.query_selector_all('button:has(.anticon-copy)')
        print(f"  Botoes com anticon-copy: {len(copy_btns)}")
        
        if len(copy_btns) > 0:
            await copy_btns[0].click()
            await asyncio.sleep(2)
            await ss(page, '10_modal_lojas_aberto')
            
            modal = await page.query_selector('.ant-modal-content')
            if modal:
                # Diagnosticar estrutura do modal
                modal_info = await page.evaluate('''() => {
                    const modal = document.querySelector('.ant-modal-content');
                    if (!modal) return {error: 'modal nao encontrado'};
                    
                    const thead = modal.querySelector('thead');
                    const theadCheckboxes = modal.querySelectorAll('thead input[type="checkbox"]');
                    const theadWrappers = modal.querySelectorAll('thead .ant-checkbox-wrapper');
                    const tbodyRows = modal.querySelectorAll('tbody tr');
                    const tbodyCheckboxes = modal.querySelectorAll('tbody input[type="checkbox"]');
                    const tbodyChecked = modal.querySelectorAll('tbody .ant-checkbox-checked');
                    const allChecked = modal.querySelectorAll('.ant-checkbox-checked');
                    
                    // Tentar achar o checkbox "minus" (indeterminado)
                    const indeterminate = modal.querySelectorAll('.ant-checkbox-indeterminate');
                    
                    return {
                        hasThead: !!thead,
                        theadCheckboxCount: theadCheckboxes.length,
                        theadWrapperCount: theadWrappers.length,
                        tbodyRowCount: tbodyRows.length,
                        tbodyCheckboxCount: tbodyCheckboxes.length,
                        tbodyCheckedCount: tbodyChecked.length,
                        allCheckedCount: allChecked.length,
                        indeterminateCount: indeterminate.length,
                        // HTML do thead para debug
                        theadHTML: thead ? thead.innerHTML.substring(0, 500) : 'SEM THEAD',
                    };
                }''')
                print(f"  Modal info: {modal_info}")
                
                # Tentar clicar no checkbox do header
                print("\n=== 12. CLICANDO SELECT ALL ===")
                header_chk = await modal.query_selector('thead .ant-checkbox-wrapper')
                if header_chk:
                    print("  Encontrado thead .ant-checkbox-wrapper, clicando...")
                    await header_chk.click(force=True)
                    await asyncio.sleep(1)
                else:
                    print("  thead .ant-checkbox-wrapper NAO encontrado")
                    # Tentar input direto
                    header_input = await modal.query_selector('thead input[type="checkbox"]')
                    if header_input:
                        print("  Encontrado thead input[checkbox], clicando...")
                        await header_input.click(force=True)
                        await asyncio.sleep(1)
                    else:
                        print("  NENHUM checkbox de header encontrado!")
                
                await ss(page, '11_apos_select_all')
                
                # Verificar resultado
                post_info = await page.evaluate('''() => {
                    const modal = document.querySelector('.ant-modal-content');
                    const tbodyChecked = modal.querySelectorAll('tbody .ant-checkbox-checked');
                    const tbodyRows = modal.querySelectorAll('tbody tr');
                    return {
                        checked: tbodyChecked.length,
                        total: tbodyRows.length
                    };
                }''')
                print(f"  Apos Select All: {post_info['checked']}/{post_info['total']} marcados")
                
                # Se nao marcou todos, tentar iterar
                if post_info['checked'] < post_info['total']:
                    print("  FALHOU! Tentando marcar um por um...")
                    unchecked = await modal.query_selector_all('tbody tr')
                    count = 0
                    for row in unchecked:
                        chk = await row.query_selector('.ant-checkbox-wrapper')
                        if chk:
                            cls = await chk.evaluate('el => el.className')
                            if 'checked' not in cls:
                                await chk.click(force=True)
                                count += 1
                                await asyncio.sleep(0.1)
                    print(f"  Marcados individualmente: {count}")
                    
                    await ss(page, '12_apos_marcar_individual')
                    
                    # Rever
                    final_info = await page.evaluate('''() => {
                        const modal = document.querySelector('.ant-modal-content');
                        const checked = modal.querySelectorAll('tbody .ant-checkbox-checked');
                        const total = modal.querySelectorAll('tbody tr');
                        return {checked: checked.length, total: total.length};
                    }''')
                    print(f"  Estado final: {final_info['checked']}/{final_info['total']} marcados")
                
                # Fechar modal
                try: await page.click('button:has-text("Fechar")')
                except: await page.keyboard.press('Escape')
                
            else:
                print("  MODAL NAO APARECEU!")
        else:
            print("  Botao de lojas NAO encontrado! Procurando alternativas...")
            # Buscar todos os botoes e seus icones
            all_btns = await page.evaluate('''() => {
                const btns = document.querySelectorAll('button');
                return Array.from(btns).map(b => ({
                    text: b.innerText.trim().substring(0, 30),
                    iconClasses: b.querySelector('i,span[class*="icon"],span[class*="anticon"]')?.className || 'sem icone'
                })).filter(b => b.text || b.iconClasses !== 'sem icone');
            }''')
            print(f"  Todos os botoes: {all_btns}")

        print("\n=== DIAGNOSTICO COMPLETO ===")
        await browser.close()

if __name__ == '__main__':
    asyncio.run(run())
