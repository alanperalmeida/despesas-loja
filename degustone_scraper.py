"""
Script de Web Scraping para extracao de relatorios de Despesas - Degustone (Linx Degust)
Utiliza Playwright para automacao do navegador

Fluxo completo:
1. Login com CPF e teclado virtual de senha
2. Selecao de servidor e franquia via Vue Multiselect
3. Clique em "Prosseguir" para entrar no sistema
4. Navegacao via Nuxt Router para /relatorio/despesas-loja (mantendo sessao SPA)
5. Fechar popup de suporte (Claudia)
6. Alterar periodo se necessario (Suporta Range Visual 01/01/2025 a 28/02/2025)
7. Ativar toggle "Agrupar por Loja"
8. Selecionar todas as lojas (Modal Multiloja com verificacao de selecao)
9. Clicar "Consultar" -> Capturar NOVA ABA (Popup)
10. Extracao dos dados da tabela na nova aba
11. Fechar nova aba e salvar dados
"""
import asyncio
import json
import calendar
from datetime import datetime, timedelta
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser
from config import DegustoneConfig
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DegustoneScraper:
    """Scraper para extracao de relatorios do sistema Degustone"""

    def __init__(self, headless: bool = None, data_inicio: str = None, data_fim: str = None):
        """
        Args:
            headless: Se True, roda sem janela. Se False, mostra navegador.
            data_inicio: Data inicio do periodo (DD/MM/YYYY). Padrao: primeiro dia do mes.
            data_fim: Data fim do periodo (DD/MM/YYYY). Padrao: hoje.
        """
        self.config = DegustoneConfig
        self.headless = headless if headless is not None else self.config.HEADLESS
        self.browser: Browser = None
        self.page: Page = None
        self._playwright = None

        # Datas do periodo
        # Padrao: 01/01/2025 ate ultimo dia do proximo mes
        hoje = datetime.now()
        if data_inicio:
            self.data_inicio = data_inicio
        else:
            self.data_inicio = '01/01/2025'
        if data_fim:
            self.data_fim = data_fim
        else:
            # Proximo mes a partir de hoje
            if hoje.month == 12:
                prox_mes = hoje.replace(year=hoje.year + 1, month=1, day=1)
            else:
                prox_mes = hoje.replace(month=hoje.month + 1, day=1)
            ultimo_dia = calendar.monthrange(prox_mes.year, prox_mes.month)[1]
            self.data_fim = prox_mes.replace(day=ultimo_dia).strftime('%d/%m/%Y')

    async def start_browser(self):
        """Inicializa o navegador Playwright"""
        logger.info("Iniciando navegador...")
        self._playwright = await async_playwright().start()
        # args para evitar deteccao basica e permitir popups
        self.browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-setuid-sandbox'] 
        )
        self.context = await self.browser.new_context(
             viewport={'width': 1280, 'height': 800}
        )
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.config.TIMEOUT)
        logger.info("Navegador iniciado com sucesso")

    async def close_browser(self):
        """Fecha o navegador"""
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Navegador fechado")

    async def login(self):
        """
        Realiza login no sistema Degustone.
        """
        logger.info(f"Acessando pagina de login: {self.config.LOGIN_URL}")
        await self.page.goto(self.config.LOGIN_URL)
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)

        # Preencher CPF
        logger.info("Preenchendo CPF...")
        try:
            await self.page.fill('input[name="username"]', self.config.CPF, timeout=10000)
        except Exception:
            await self.page.fill('input[type="text"]', self.config.CPF, timeout=10000)
        logger.info("CPF preenchido")

        # Digitar senha via teclado virtual
        logger.info("Digitando senha via teclado virtual...")
        virtual_buttons = await self.page.query_selector_all(
            'button.ant-btn.ant-btn-primary.ant-btn-lg:not(.btn-backspace)'
        )

        digit_to_button = {}
        for btn in virtual_buttons:
            text = (await btn.inner_text()).strip()
            if ' ou ' in text:
                for part in text.split(' ou '):
                    d = part.strip()
                    if d.isdigit():
                        digit_to_button[d] = btn

        for digito in self.config.SENHA:
            if digito not in digit_to_button:
                raise Exception(f"Digito '{digito}' nao encontrado no teclado virtual")
            await digit_to_button[digito].click()
            await asyncio.sleep(0.3)
        logger.info("Senha digitada")

        # Clicar botao Entrar
        await self.page.click('button[type="submit"]')
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)

        current_url = self.page.url
        if 'login' in current_url and 'acesso' not in current_url:
            await self.page.screenshot(path='debug_login_failed.png')
            raise Exception(f"Login falhou. URL: {current_url}")

        logger.info(f"Login OK. URL: {current_url}")

    async def select_server_and_franchise(self, franquia_id: str):
        """
        Seleciona servidor e franquia na pagina /acesso.
        """
        logger.info("Selecionando servidor e franquia...")

        await self.page.wait_for_selector('[role="combobox"]', timeout=15000)
        await asyncio.sleep(2)

        comboboxes = await self.page.query_selector_all('[role="combobox"]')
        if len(comboboxes) < 2:
            raise Exception(f"Esperados 2 comboboxes, encontrados {len(comboboxes)}")

        # ====== SERVIDOR ======
        logger.info("Selecionando servidor...")
        await comboboxes[0].click()
        await asyncio.sleep(1)

        options = await self.page.query_selector_all('.multiselect__element')
        if options:
            text = (await options[0].inner_text()).strip()
            await options[0].click()
            logger.info(f"Servidor selecionado: {text}")
        else:
            raise Exception("Nenhuma opcao de servidor encontrada")

        await asyncio.sleep(2)

        # ====== FRANQUIA ======
        franquia_nome = self.config.get_franquia_nome(franquia_id)
        logger.info(f"Selecionando franquia: {franquia_id} ({franquia_nome})...")

        comboboxes = await self.page.query_selector_all('[role="combobox"]')
        await comboboxes[1].click()
        await asyncio.sleep(1)

        options = await self.page.query_selector_all('.multiselect__element')
        
        franquia_found = False
        for opt in options:
            text = (await opt.inner_text()).strip()
            if (franquia_nome.upper() in text.upper() or
                franquia_id in text or
                text.upper() == franquia_nome.upper()):
                await opt.click()
                franquia_found = True
                logger.info(f"Franquia selecionada: {text}")
                break

        if not franquia_found:
            raise Exception(f"Franquia '{franquia_nome}' ({franquia_id}) nao encontrada")

        await asyncio.sleep(1)

        # ====== PROSSEGUIR ======
        logger.info("Clicando em Prosseguir...")
        try:
            await self.page.click('button:has-text("Prosseguir")', timeout=10000)
        except Exception:
            await self.page.click('button.ant-btn-secondary', timeout=10000)

        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(5)

    async def close_popups(self):
        """Fecha popup de suporte (Claudia de Moura de Macedo)"""
        try:
            xmark = await self.page.query_selector('.fa-xmark')
            if xmark:
                vis = await xmark.is_visible()
                if vis:
                    await xmark.click()
                    logger.info("Popup de suporte fechado")
                    await asyncio.sleep(1)
        except Exception:
            pass

    async def navigate_to_report(self):
        """Navega para pagina de relatorio via Nuxt router"""
        logger.info("Navegando para relatorio de despesas...")
        
        # Fecha popups antes
        await self.close_popups()

        await self.page.evaluate(
            '() => { window.$nuxt.$router.push("/relatorio/despesas-loja"); }'
        )
        await asyncio.sleep(5)
        
        # Fecha popups depois
        await self.close_popups()

    async def select_all_stores(self):
        """Seleciona todas as lojas via Drawer Multiloja usando JS direto"""
        logger.info("Selecionando todas as lojas...")
        try:
            # Botao de lojas e o PRIMEIRO button:has(.anticon-copy) na pagina (header)
            copy_btn = await self.page.query_selector('button:has(.anticon-copy)')
            if not copy_btn:
                logger.warning("Botao de selecao de lojas nao encontrado")
                return
            
            await copy_btn.click()
            await asyncio.sleep(2)
            
            # O componente Multiloja usa um ANT-DRAWER com tabela customizada (Vxe Grid)
            # Os checkboxes sao input[type=checkbox] nativos, NAO .ant-checkbox-wrapper
            drawer = await self.page.query_selector('.ant-drawer.ant-drawer-open')
            if not drawer:
                drawer = await self.page.query_selector('.ant-drawer')
            
            if not drawer:
                logger.error("Drawer Multiloja nao abriu!")
                return
            
            logger.info("Drawer Multiloja aberto com sucesso")
            await self.page.screenshot(path='debug_drawer_aberto.png')
            
            # Usar JavaScript para clicar em todos os checkboxes nao marcados
            # A tabela do Multiloja usa componentes Vxe com inputs nativos
            result = await self.page.evaluate('''() => {
                const drawer = document.querySelector('.ant-drawer.ant-drawer-open');
                if (!drawer) return {error: 'drawer nao encontrado'};
                
                // Encontrar todos os checkboxes dentro do drawer
                const allCheckboxes = drawer.querySelectorAll('input[type="checkbox"]');
                let total = 0;
                let clicked = 0;
                
                for (const cb of allCheckboxes) {
                    // Pular o header checkbox (geralmente o primeiro)
                    // Verificar se esta numa linha de dados
                    const row = cb.closest('tr');
                    if (!row) continue;
                    
                    // Se esta no thead, pode ser o "select all" - vamos tentar clicar se nao estiver checked
                    if (row.closest('thead')) {
                        // Este e o header checkbox - ignorar por enquanto
                        continue;
                    }
                    
                    total++;
                    if (!cb.checked) {
                        cb.click();
                        clicked++;
                    }
                }
                
                // Se nenhum checkbox de dados foi encontrado, tentar abordagem mais ampla
                if (total === 0) {
                    // Tentar clicar no checkbox do header para selecionar todos
                    const headerCb = drawer.querySelector('input[type="checkbox"]');
                    if (headerCb) {
                        if (!headerCb.checked) {
                            headerCb.click();
                            return {method: 'header_click', headerChecked: true};
                        } else {
                            // Desmarcar e remarcar para forcar selecao
                            headerCb.click();
                            headerCb.click();
                            return {method: 'header_toggle', headerChecked: true};
                        }
                    }
                    return {error: 'nenhum checkbox encontrado', totalInputs: allCheckboxes.length};
                }
                
                return {total: total, clicked: clicked, alreadyChecked: total - clicked};
            }''')
            
            logger.info(f"Resultado selecao lojas: {result}")
            
            # Se a abordagem por linhas nao funcionou, tentar o header checkbox
            if result.get('total', 0) == 0 or result.get('error'):
                logger.warning(f"Primeira tentativa: {result}. Tentando header checkbox...")
                
                # Clicar no primeiro checkbox do drawer (header - select all)
                header_result = await self.page.evaluate('''() => {
                    const drawer = document.querySelector('.ant-drawer.ant-drawer-open');
                    if (!drawer) return 'no drawer';
                    
                    // O header checkbox geralmente esta na primeira posicao
                    const headerCb = drawer.querySelector('input[type="checkbox"]');
                    if (!headerCb) return 'no header checkbox';
                    
                    // Se indeterminado ou nao marcado, clicar
                    // Primeiro clicar para desmarcar tudo (se indeterminado)
                    headerCb.click();
                    
                    // Esperar um pouco e clicar de novo para marcar tudo
                    setTimeout(() => headerCb.click(), 300);
                    
                    return 'header clicked twice';
                }''')
                logger.info(f"Header checkbox: {header_result}")
                await asyncio.sleep(1)
            
            await self.page.screenshot(path='debug_lojas_selecionadas.png')
            
            # Fechar Drawer
            close_btn = await self.page.query_selector('button:has-text("Fechar")')
            if close_btn:
                await close_btn.click()
            else:
                await self.page.keyboard.press('Escape')
            
            await asyncio.sleep(1)
            logger.info("Selecao de lojas concluida")
            
        except Exception as e:
            logger.error(f"Erro ao selecionar todas as lojas: {e}")
            import traceback
            traceback.print_exc()

    async def toggle_group_by_store(self):
        """Ativa o toggle 'Agrupar por Loja' (NAO o toggle 'Agrupar' generico)"""
        logger.info("Ativando 'Agrupar por Loja'...")
        try:
            # CUIDADO: existem 2 toggles lado a lado:
            # - "Agrupar" (generico) 
            # - "Agrupar por Loja" (o que queremos)
            # Cada label esta dentro de um ant-col separado, com seu proprio switch
            switch_found = await self.page.evaluate('''() => {
                // Buscar ESPECIFICAMENTE o label com texto exato "Agrupar por Loja"
                const labels = document.querySelectorAll('label');
                for (const label of labels) {
                    if (label.textContent.trim() === 'Agrupar por Loja') {
                        // O switch esta no mesmo ant-form-item que o label
                        // Estrutura: ant-col > ant-form-item > [ant-form-item-label > label] + [ant-form-item-control > switch]
                        const formItem = label.closest('.ant-row.ant-form-item') || label.closest('.ant-form-item');
                        if (formItem) {
                            const sw = formItem.querySelector('.ant-switch');
                            if (sw) {
                                if (!sw.classList.contains('ant-switch-checked')) {
                                    sw.click();
                                    return 'clicked_in_form_item';
                                }
                                return 'already_checked';
                            }
                        }
                        
                        // Fallback: buscar o switch mais proximo subindo pela hierarquia
                        let el = label;
                        for (let i = 0; i < 5; i++) {
                            el = el.parentElement;
                            if (!el) break;
                            // Buscar switch DIRETO dentro deste nivel (nao descendente profundo)
                            const sw = el.querySelector(':scope > .ant-col .ant-switch, :scope > .ant-switch');
                            if (sw) {
                                if (!sw.classList.contains('ant-switch-checked')) {
                                    sw.click();
                                    return 'clicked_via_parent';
                                }
                                return 'already_checked';
                            }
                        }
                    }
                }
                return false;
            }''')
            if switch_found and switch_found != False:
                logger.info(f"Toggle 'Agrupar por Loja': {switch_found}")
            else:
                logger.warning("Toggle 'Agrupar por Loja' nao encontrado")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Erro ao ativar toggle: {e}")

    async def set_period(self):
        """Configura o periodo de consulta com navegacao visual explicita (<< e <)"""
        logger.info(f"Configurando periodo: {self.data_inicio} a {self.data_fim}")
        
        try:
            picker = await self.page.query_selector('.ant-calendar-picker')
            if not picker:
                logger.warning("Picker de data nao encontrado")
                return
                
            await picker.click(force=True)
            await asyncio.sleep(1)
            
            dt_ini = datetime.strptime(self.data_inicio, '%d/%m/%Y')
            dt_fim = datetime.strptime(self.data_fim, '%d/%m/%Y')
            now = datetime.now()
            
            # Helper para pegar ano e mes do calendario
            async def get_cal_info():
                y_el = await self.page.query_selector('.ant-calendar-year-select')
                y = int((await y_el.inner_text()).strip()) if y_el else now.year
                
                m_el = await self.page.query_selector('.ant-calendar-month-select')
                m_txt = (await m_el.inner_text()).lower().strip() if m_el else ''
                meses = ['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez']
                m = meses.index(m_txt) + 1 if m_txt in meses else now.month
                return y, m

            # --- DATA INICIO ---
            # 1. Navegar Ano (<<)
            curr_year, curr_month = await get_cal_info()
            
            while curr_year > dt_ini.year:
                logger.info(f"Ano {curr_year} > {dt_ini.year}. Voltando ano (<<)")
                btn = await self.page.query_selector('.ant-calendar-prev-year-btn')
                if btn: await btn.click(); await asyncio.sleep(0.5)
                else: break
                curr_year, _ = await get_cal_info()

            # 2. Navegar Mes (< ou >)
            while curr_month != dt_ini.month:
                if curr_month > dt_ini.month:
                    btn = await self.page.query_selector('.ant-calendar-prev-month-btn')
                else:
                    btn = await self.page.query_selector('.ant-calendar-next-month-btn')
                
                if btn: await btn.click(); await asyncio.sleep(0.3)
                _, new_m = await get_cal_info()
                if new_m == curr_month: break # Safety break
                curr_month = new_m

            # 3. Clicar Dia Inicio
            logger.info(f"Clicando dia inicio: {dt_ini.day}")
            await self.page.evaluate(f'''(day) => {{
                const tds = document.querySelectorAll('.ant-calendar-range-part tr td.ant-calendar-cell:not(.ant-calendar-next-month-cell):not(.ant-calendar-last-month-cell)');
                for (const td of tds) {{
                    if (td.innerText.trim() == day) {{ td.click(); return; }}
                }}
            }}''', str(dt_ini.day))
            await asyncio.sleep(1)

            # --- DATA FIM ---
            # Navegar ate o mes/ano correto da data fim
            # Re-query do botao a cada clique para evitar stale element
            diff_months = (dt_fim.year - dt_ini.year) * 12 + (dt_fim.month - dt_ini.month)
            
            if diff_months > 0:
                logger.info(f"Navegando {diff_months} meses a frente para data fim...")
                for i in range(diff_months):
                    # RE-QUERY a cada iteracao (evita Element not attached to DOM)
                    next_btn = await self.page.query_selector('.ant-calendar-next-month-btn')
                    if next_btn:
                        await next_btn.click()
                        await asyncio.sleep(0.3)
                    else:
                        logger.warning(f"Botao proximo mes perdido na iteracao {i}")
                        break
            elif diff_months < 0:
                # Caso a data fim seja ANTES da data inicio (improvavel, mas seguro)
                for i in range(abs(diff_months)):
                    prev_btn = await self.page.query_selector('.ant-calendar-prev-month-btn')
                    if prev_btn:
                        await prev_btn.click()
                        await asyncio.sleep(0.3)
                    else:
                        break

            # Clicar Dia Fim
            logger.info(f"Clicando dia fim: {dt_fim.day}")
            await self.page.evaluate(f'''(day) => {{
                // Recapturar elementos pois DOM mudou
                const tds = document.querySelectorAll('.ant-calendar-range-part tr td.ant-calendar-cell:not(.ant-calendar-next-month-cell):not(.ant-calendar-last-month-cell)');
                for (const td of tds) {{
                    if (td.innerText.trim() == day) {{ td.click(); return; }}
                }}
            }}''', str(dt_fim.day))
            await asyncio.sleep(1)

        except Exception as e:
            logger.warning(f"Erro ao configurar periodo visualmente: {e}")

    async def click_consultar_and_get_page(self):
        """Clica no botao Consultar e retorna a nova pagina (popup) se abrir"""
        logger.info("Clicando em Consultar...")
        await self.close_popups()
        
        try:
            # Timeout maior para relatorios grandes (16 lojas, 14+ meses)
            async with self.page.context.expect_page(timeout=60000) as new_page_info:
                consultar_btn = await self.page.query_selector('button:has-text("Consultar")')
                if consultar_btn:
                    await consultar_btn.click(force=True)
                else:
                    await self.page.evaluate('''() => {
                        const btns = document.querySelectorAll('button');
                        for (const btn of btns) {
                            if (btn.textContent.includes('Consultar')) btn.click();
                        }
                    }''')
            
            logger.info("Botao Consultar clicado. Aguardando nova aba...")
            new_page = await new_page_info.value
            
            # Esperar carregamento
            try:
                await new_page.wait_for_load_state('load', timeout=60000)
                logger.info(f"Nova aba carregada (load): {new_page.url}")
            except Exception as e:
                logger.warning(f"Timeout no load: {e}")
            
            # CAPTURAR IMEDIATAMENTE - a aba .aspx se auto-fecha em ~10s!
            logger.info("Capturando dados do relatorio IMEDIATAMENTE (aba .aspx auto-fecha)...")
            
            return new_page
        except Exception as e:
            logger.error(f"Nova aba nao detectada: {e}")
            return None

    # ... extract_report e save_report mantidos iguais (uso de self.save_report na funcao run) ...
    # Para brevidade do replace, vou reincluir os metodos auxiliares necessarios
    async def extract_report(self, page_target: Page, franquia_id: str):
        output_dir = self.config.ensure_output_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # PRIORIDADE: capturar HTML IMEDIATAMENTE (a aba .aspx se auto-fecha em ~10s!)
        html_content = await page_target.content()
        logger.info(f"HTML capturado: {len(html_content)} bytes")
        
        # Tentar screenshot (pode falhar se aba fechar durante)
        screenshot_path = output_dir / f'relatorio_franquia_{franquia_id}_{timestamp}.png'
        try:
            await page_target.screenshot(path=str(screenshot_path), full_page=True)
        except: 
            logger.warning("Screenshot falhou (aba pode ter fechado)")

        report_data = {
            'franquia_id': franquia_id,
            'franquia_nome': self.config.get_franquia_nome(franquia_id),
            'timestamp': datetime.now().isoformat(),
            'periodo_inicio': self.data_inicio,
            'periodo_fim': self.data_fim,
            'url': page_target.url if not page_target.is_closed() else 'N/A',
            'screenshot': str(screenshot_path),
            'tables': [],
        }

        # Parsear tabelas OFFLINE a partir do HTML raw (sem depender da aba aberta)
        report_data['tables'] = self._parse_tables_from_html(html_content)
        
        # Extrair texto do body via regex simples (sem depender da aba)
        import re
        body_match = re.search(r'<body[^>]*>(.*)</body>', html_content, re.DOTALL | re.IGNORECASE)
        body_text = re.sub(r'<[^>]+>', ' ', body_match.group(1)).strip() if body_match else ''
        
        return report_data, body_text, html_content, timestamp

    def _parse_tables_from_html(self, html_content: str) -> list:
        """Parseia tabelas do HTML raw sem precisar da pagina aberta"""
        from html.parser import HTMLParser
        
        class TableParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.tables = []
                self.current_table = None
                self.current_row = None
                self.current_cell = ''
                self.in_thead = False
                self.in_cell = False
                self.cell_tag = None
            
            def handle_starttag(self, tag, attrs):
                tag = tag.lower()
                if tag == 'table':
                    self.current_table = {'headers': [], 'rows': []}
                elif tag == 'thead':
                    self.in_thead = True
                elif tag == 'tr':
                    self.current_row = []
                elif tag in ('td', 'th'):
                    self.in_cell = True
                    self.cell_tag = tag
                    self.current_cell = ''
            
            def handle_endtag(self, tag):
                tag = tag.lower()
                if tag == 'table' and self.current_table:
                    if self.current_table['rows']:
                        self.tables.append(self.current_table)
                    self.current_table = None
                elif tag == 'thead':
                    self.in_thead = False
                elif tag == 'tr' and self.current_row is not None and self.current_table:
                    if self.in_thead or (not self.current_table['headers'] and self.cell_tag == 'th'):
                        self.current_table['headers'] = self.current_row
                    else:
                        if self.current_row:
                            self.current_table['rows'].append(self.current_row)
                    self.current_row = None
                elif tag in ('td', 'th'):
                    if self.in_cell and self.current_row is not None:
                        self.current_row.append(self.current_cell.strip())
                    self.in_cell = False
            
            def handle_data(self, data):
                if self.in_cell:
                    self.current_cell += data
        
        parser = TableParser()
        parser.feed(html_content)
        
        result = []
        for i, table in enumerate(parser.tables):
            if table['rows']:
                result.append({
                    'table_index': i,
                    'headers': table['headers'],
                    'rows': table['rows'],
                    'total_rows': len(table['rows'])
                })
        
        logger.info(f"Parsed {len(result)} tabelas do HTML offline")
        return result

    async def save_report(self, report_data: dict, body_text: str, html_content: str, timestamp: str):
        output_dir = self.config.ensure_output_dir()
        fid = report_data.get('franquia_id', 'unknown')
        base = f'relatorio_franquia_{fid}_{timestamp}'
        json_path = output_dir / f'{base}.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        with open(output_dir / f'{base}.html', 'w', encoding='utf-8') as f: f.write(html_content)
        with open(output_dir / f'{base}.txt', 'w', encoding='utf-8') as f: f.write(body_text)
        return json_path

    async def run(self, franquia_id: str = None):
        try:
            self.config.validate()
            await self.start_browser()
            await self.login()
            franquias = [franquia_id] if franquia_id else self.config.get_franquias_list()
            results = []

            for idx, fid in enumerate(franquias):
                logger.info(f"Processando franquia: {fid}")
                try:
                    await self.select_server_and_franchise(fid)
                    await self.navigate_to_report()
                    await self.set_period()
                    await self.toggle_group_by_store()
                    await self.select_all_stores()
                    
                    report_page = await self.click_consultar_and_get_page()
                    if report_page:
                        report_data, body, html, ts = await self.extract_report(report_page, fid)
                        await report_page.close()
                        path = await self.save_report(report_data, body, html, ts)
                        results.append({'franquia_id': fid, 'status': 'success', 'tables': len(report_data['tables']), 'file': str(path)})
                    else:
                        raise Exception("Falha ao abrir aba de relatorio")
                except Exception as e:
                    logger.error(f"Erro: {e}")
                    results.append({'franquia_id': fid, 'status': 'error', 'error': str(e)})

                if idx < len(franquias) - 1:
                    try: await self.page.goto(self.config.ACESSO_URL); await asyncio.sleep(5)
                    except: pass
            
            return results
        except Exception as e:
            logger.error(f"Critico: {e}")
            raise
        finally:
            await self.close_browser()

async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--franquia', type=str)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--data-inicio', type=str)
    parser.add_argument('--data-fim', type=str)
    args = parser.parse_args()

    scraper = DegustoneScraper(
        headless=args.headless,
        data_inicio=args.data_inicio,
        data_fim=args.data_fim,
    )
    results = await scraper.run(franquia_id=args.franquia)
    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    asyncio.run(main())
