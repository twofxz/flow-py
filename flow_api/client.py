"""
FlowClient - Gerencia conexão CDP, perfil persistente e abas ativas do Google Flow.
"""

import os
import time
import socket
import subprocess
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

DEFAULT_CDP_URL = "http://127.0.0.1:9222"
DEFAULT_PROFILE = r"C:\Users\FALA MUITO\.cache\chrome-devtools-mcp\chrome-profile"
CHROME_BIN = r"C:\Users\FALA MUITO\chrome\win64-153.0.8010.47\chrome-win64\chrome.exe"
FLOW_BASE_URL = "https://flow.google.com"

class FlowClient:
    def __init__(self, cdp_url: str = DEFAULT_CDP_URL, download_dir: Optional[str] = None):
        self.cdp_url = cdp_url
        self.download_dir = download_dir or os.path.expanduser(r"~\Downloads\google_flow_assets")
        os.makedirs(self.download_dir, exist_ok=True)
        
        self._playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
    def start_browser_if_needed(self):
        """Verifica a porta 9222 e inicia o Chromium persistente se necessário."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 9222))
        sock.close()
        
        if result != 0:
            print("[FlowClient] Navegador não detectado na porta 9222. Iniciando processo...")
            cmd = [
                CHROME_BIN,
                "--remote-debugging-port=9222",
                f"--user-data-dir={DEFAULT_PROFILE}",
                "--no-first-run",
                "--no-default-browser-check",
                FLOW_BASE_URL
            ]
            subprocess.Popen(cmd)
            time.sleep(3)

    def connect(self) -> Page:
        """Conecta ao Chromium via CDP e sincroniza a aba do Google Flow."""
        self.start_browser_if_needed()
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.connect_over_cdp(self.cdp_url)
        self.context = self.browser.contexts[0]
        
        target_page = None
        for page in self.context.pages:
            if "flow.google.com/project" in page.url:
                target_page = page
                break
                
        if not target_page:
            for page in self.context.pages:
                if "flow.google.com" in page.url:
                    target_page = page
                    break
                    
        if not target_page:
            target_page = self.context.new_page()
            target_page.goto(FLOW_BASE_URL)
            target_page.wait_for_load_state("networkidle")
            
        self.page = target_page
        self.page.bring_to_front()
        self.dismiss_modals()
        
        # Se estiver na página inicial do Flow, clica em 'Novo projeto'
        if "flow.google.com/project" not in self.page.url:
            new_btn = self.page.locator("button:has-text('Novo projeto'), [aria-label*='Novo projeto']").first
            if new_btn.is_visible():
                print("[FlowClient] Abrindo novo projeto no Flow...")
                new_btn.click()
                time.sleep(2.5)
                self.dismiss_modals()
                
        self.set_download_path(self.download_dir)
        return self.page

    def dismiss_modals(self):
        """Descarta modais, popups de novidades ou diálogos."""
        if not self.page:
            return
        time.sleep(0.5)
        comecar_btn = self.page.locator("button:has-text('Começar'), button:has-text('Entendi')").first
        if comecar_btn.is_visible():
            comecar_btn.click()
            time.sleep(1)
        else:
            self.page.keyboard.press("Escape")

    def ensure_canvas(self):
        """Garante que a visualização esteja no canvas principal fechando o visualizador se aberto."""
        if not self.page:
            return
        concluir_btn = self.page.locator("button:has-text('Concluir')").first
        if concluir_btn.is_visible():
            concluir_btn.click()
            time.sleep(1.5)

    def set_download_path(self, path: str):
        """Configura dinamicamente a pasta de downloads via sessão CDP."""
        self.download_dir = path
        os.makedirs(self.download_dir, exist_ok=True)
        if self.page:
            cdp = self.page.context.new_cdp_session(self.page)
            cdp.send("Page.setDownloadBehavior", {
                "behavior": "allow",
                "downloadPath": self.download_dir
            })

    def close(self):
        """Finaliza a sessão do cliente Playwright mantendo o navegador ativo."""
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
