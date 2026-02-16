"""
Script de Web Scraping para Degustone - Versao Corrigida (Navegacao Visual Explicita)
"""
import asyncio
import json
import logging
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser
from config import DegustoneConfig

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DegustoneScraper:
    def __init__(self, headless: bool = None, data_inicio: str = None, data_fim: str = None):
        self.config = DegustoneConfig
        self.headless = headless if headless is not None else self.config.HEADLESS
        self.data_inicio = data_inicio or datetime.now().replace(day=1).strftime('%d/%m/%Y')
        self.data_fim = data_fim or datetime.now().strftime('%d/%m/%Y')
        self.browser = None
        self.page = None

    async def start_browser(self):
        logger.info("Iniciando navegador...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.context = await self.browser.new_context(viewport={'width': 1280, 'height': 800})
        self.page = await self.context.new_page()
        self.page.set_default_timeout(45000) # Timeout maior

    async def close_browser(self):
        if self.browser: await self.browser.close()
        if hasattr(self, 'playwright'): await self.playwright.stop()

    async def login(self):
        logger.info(f"Login em {self.config.LOGIN_URL}")
        await self.page.goto(self.config.LOGIN_URL)
        
        # CPF
        try: await self.page.fill('input[name="username"]', self.config.CPF, timeout=5000)
        except: await self.page.fill('input[type="text"]', self.config.CPF)
        
        # Senha Virtual
        buttons = await self.page.query_selector_all('button.ant-btn')
        digit_map = {}
        for btn in buttons:
            txt = await btn.inner_text()
            if ' ou ' in txt:
                for part in txt.split(' ou '):
                    if part.strip().isdigit(): digit_map[part.strip()] = btn
        
        for digit in self.config.SENHA:
            await digit_map[digit].click()
            await asyncio.sleep(0.2)
            
        await self.page.click('button[type="submit"]')
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)

    async def select_franchise(self, franquia_id):
        logger.info(f"Selecionando franquia {franquia_id}...")
        await self.page.wait_for_selector('[role="combobox"]', state='visible')
        
        combos = await self.page.query_selector_all('[role="combobox"]')
        # 1. Servidor
        await combos[0].click()
        await asyncio.sleep(0.5)
        await self.page.click('.multiselect__element') # Primeiro (Producao)
        await asyncio.sleep(1)
        
        # 2. Franquia
        franquia_nome = self.config.get_franquia_nome(franquia_id)
        await combos[1].click()
        await asyncio.sleep(1)
        
        options = await self.page.query_selector_all('.multiselect__element')
        found = False
        for opt in options:
            txt = (await opt.inner_text()).upper()
            if franquia_nome.upper() in txt or franquia_id in txt:
                await opt.click()
                found = True
                break
        
        if not found: logger.warning(f"Franquia {franquia_id} nao encontrada na lista!")
        
        await asyncio.sleep(1)
        try: await self.page.click('button:has-text("Prosseguir")')
        except: await self.page.click('button.ant-btn-secondary')
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(5)

    async def extract_report_popup(self):
        # Clicar Consultar e capturar Popup
        logger.info("Clicando Consultar...")
        
        # Fechar qualquer popup de suporte antes
        try: await self.page.click('.fa-xmark', timeout=1000)
        except: pass

        async with self.page.context.expect_page(timeout=20000) as new_page_info:
            btn = await self.page.query_selector('button:has-text("Consultar")')
            if btn: await btn.click(force=True)
            else: 
                # Fallback JS
                await self.page.evaluate("document.querySelectorAll('button').forEach(b => b.textContent.includes('Consultar') && b.click())")
        
        new_page = await new_page_info.value
        await new_page.wait_for_load_state()
        logger.info(f"Popup aberto: {new_page.url}")
        return new_page

    async def select_dates_visual(self):
        """Usa navegação visual explicita (<< e <)"""
        logger.info(f"Configurando datas: {self.data_inicio} a {self.data_fim}")
        
        picker = await self.page.query_selector('.ant-calendar-picker')
        if not picker: return
        await picker.click(force=True)
        await asyncio.sleep(1)
        
        dt_ini = datetime.strptime(self.data_inicio, '%d/%m/%Y')
        dt_fim = datetime.strptime(self.data_fim, '%d/%m/%Y')
        now = datetime.now()
        
        # --- SELECIONAR INICIO ---
        # 1. Navegar Ano (<<)
        # Assumindo que o calendario abre no ano atual (2026)
        # Se range for anterior, clicar em <<
        # Melhor: Ler o header do calendario
        
        async def get_cal_year():
            el = await self.page.query_selector('.ant-calendar-year-select')
            return int((await el.inner_text()).strip()) if el else now.year

        async def get_cal_month(): # 1-12
            el = await self.page.query_selector('.ant-calendar-month-select')
            # Texto ex: "jan", "fev"... converter
            txt = (await el.inner_text()).lower().strip() if el else ''
            meses = ['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez']
            return meses.index(txt) + 1 if txt in meses else now.month

        # Navegar para Ano de Inicio
        curr_year = await get_cal_year()
        while curr_year > dt_ini.year:
            logger.info(f"Ano atual {curr_year} > Alvo {dt_ini.year}. Clicando <<")
            prev = await self.page.query_selector('.ant-calendar-prev-year-btn')
            if prev: await prev.click(); await asyncio.sleep(0.5)
            curr_year = await get_cal_year()
            if curr_year == dt_ini.year: break

        # Navegar para Mes de Inicio
        curr_month = await get_cal_month()
        # Se ano for igual, navega mes. Se ano mudou, mes reinicia? Calendar depende.
        # Vamos assumir navegaçao linear simples com < ou >
        while curr_month != dt_ini.month:
            if curr_month > dt_ini.month:
                btn = await self.page.query_selector('.ant-calendar-prev-month-btn') # <
                logger.info("Clicando <")
            else:
                btn = await self.page.query_selector('.ant-calendar-next-month-btn') # >
                logger.info("Clicando >")
            
            if btn: await btn.click(); await asyncio.sleep(0.3)
            # Atualiza
            new_m = await get_cal_month()
            if new_m == curr_month: break # Evitar loop infinito se falhar
            curr_month = new_m

        # Clicar Dia Inicio
        logger.info(f"Clicando dia {dt_ini.day}")
        await self.page.evaluate(f'''(day) => {{
            const tds = document.querySelectorAll('.ant-calendar-range-part tr td.ant-calendar-cell:not(.ant-calendar-next-month-cell):not(.ant-calendar-last-month-cell)');
            for (const td of tds) {{
                if (td.innerText.trim() == day) {{ td.click(); return; }}
            }}
        }}''', str(dt_ini.day))
        await asyncio.sleep(1)

        # --- SELECIONAR FIM ---
        # Apos clicar inicio, o calendario pode esperar o fim.
        # Se o fim for em outro mes, navegar.
        # Calcular diferenca de meses
        diff_months = (dt_fim.year - dt_ini.year) * 12 + (dt_fim.month - dt_ini.month)
        
        if diff_months > 0:
            logger.info(f"Navegando {diff_months} meses a frente para data fim...")
            next_btn = await self.page.query_selector('.ant-calendar-next-month-btn')
            for _ in range(diff_months):
                if next_btn: await next_btn.click(); await asyncio.sleep(0.5)
        
        # Clicar Dia Fim
        logger.info(f"Clicando dia fim {dt_fim.day}")
        await self.page.evaluate(f'''(day) => {{
            // Pegar celulas validas novamente
            const tds = document.querySelectorAll('.ant-calendar-range-part tr td.ant-calendar-cell:not(.ant-calendar-next-month-cell):not(.ant-calendar-last-month-cell)');
            for (const td of tds) {{
                if (td.innerText.trim() == day) {{ td.click(); return; }}
            }}
        }}''', str(dt_fim.day))
        await asyncio.sleep(1)

    async def select_all_stores_robust(self):
        """Selecao teimosa de lojas"""
        logger.info("Abrindo modal de lojas...")
        
        # Tentar abrir modal com seletor robusto
        try:
            await self.page.click('button:has(.anticon-copy)', timeout=3000)
        except:
            logger.warning("Botao copy nao clicavel diretamente. Tentando buscar todos os botoes...")
            btns = await self.page.query_selector_all('button')
            for btn in btns:
                if await btn.query_selector('.anticon-copy'):
                    await btn.click()
                    break
        
        await asyncio.sleep(2)
        
        modal = await self.page.query_selector('.ant-modal-content')
        if not modal:
            logger.error("Modal nao abriu!")
            return

        logger.info("Modal aberto. Tentando 'Selecionar Todos'...")
        
        # Estrateg: Clicar no checkbox do Header
        header_chk = await modal.query_selector('thead .ant-checkbox-wrapper')
        if header_chk:
            await header_chk.click(force=True)
            await asyncio.sleep(1)
            
        # VERIFICAR se marcou tudo
        # Contar total de linhas vs marcados
        total = await modal.query_selector_all('tbody tr')
        checked = await modal.query_selector_all('tbody .ant-checkbox-checked')
        
        if len(checked) < len(total):
            logger.warning(f"Apenas {len(checked)}/{len(total)} marcados. Forcando um por um...")
            # Clicar nos desmarcados
            unchecked = await modal.query_selector_all('tbody .ant-checkbox-wrapper:not(.ant-checkbox-wrapper-checked)')
            for chk in unchecked:
                # Verificar se ja nao ta marcado (classe as vezes esta no span interno)
                # Melhor: clicar sempre que nao tiver a classe checked no span inner
                cls = await chk.get_attribute('class')
                if 'checked' not in cls:
                    await chk.click(force=True)
        
        logger.info("Lojas selecionadas.")
        # Fechar modal
        btns = await modal.query_selector_all('button')
        for b in btns:
             if 'Fechar' in await b.inner_text(): await b.click(); break

    async def run(self, franquia_id=None):
        await self.start_browser()
        try:
            await self.login()
            
            # Navegar
            if not franquia_id: franquia_id = '1866' # Default teste
            
            await self.select_franchise(franquia_id)
            
            # Navegar Relatorio
            try: await self.page.click('.fa-xmark', timeout=1000)
            except: pass
            await self.page.evaluate('() => window.$nuxt.$router.push("/relatorio/despesas-loja")')
            await asyncio.sleep(5)
            
            # Configurar
            await self.select_dates_visual()
            
            # Toggle Agrupar
            try: 
                 lbl = await self.page.query_selector('text="Agrupar por Loja"')
                 if lbl: await lbl.click() # Clicar no label as vezes ativa o switch irmao
            except: pass

            await self.select_all_stores_robust()
            
            # Extrair
            page_rel = await self.extract_report_popup()
            
            # Salvar basico
            await page_rel.screenshot(path="resultado_final_popup.png")
            logger.info("Sucesso! Screenshot salvo.")
            
            await page_rel.close()
            
        finally:
            await self.close_browser()

if __name__ == '__main__':
    scraper = DegustoneScraper(
        data_inicio='01/01/2025',
        data_fim='28/02/2025',
        headless=True 
    )
    asyncio.run(scraper.run('1866'))
