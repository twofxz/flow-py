"""
FlowClient - Orquestrador de conexão CDP e detecção de navegadores multiplataforma.
"""

import os
import sys
import time
import socket
import subprocess
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

DEFAULT_CDP_PORT = 9222
DEFAULT_CDP_URL = f"http://127.0.0.1:{DEFAULT_CDP_PORT}"
FLOW_BASE_URL = "https://flow.google.com"

def get_default_profile_dir() -> str:
    """Retorna diretório padrão para persistência de sessão do usuário."""
    home = os.path.expanduser("~")
    profile = os.path.join(home, ".google-flow", "profile")
    os.makedirs(profile, exist_ok=True)
    return profile

def find_chrome_binary() -> Optional[str]:
    """Detecta automaticamente o executável do Google Chrome ou Chromium no sistema."""
    # 1. Variável de ambiente explícita
    if os.environ.get("CHROME_PATH") and os.path.exists(os.environ["CHROME_PATH"]):
        return os.environ["CHROME_PATH"]
        
    # 2. Windows
    if sys.platform == "win32":
        candidates = [
            r"C:\Users\FALA MUITO\chrome\win64-153.0.8010.47\chrome-win64\chrome.exe",
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
                
    # 3. macOS
    elif sys.platform == "darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
                
    # 4. Linux
    elif sys.platform.startswith("linux"):
        import shutil
        for name in ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium"]:
            path = shutil.which(name)
            if path:
                return path
                
    return None

class FlowClient:
    def __init__(self, cdp_url: str = DEFAULT_CDP_URL, download_dir: Optional[str] = None, user_data_dir: Optional[str] = None):
        self.cdp_url = cdp_url
        self.user_data_dir = user_data_dir or get_default_profile_dir()
        self.download_dir = download_dir or os.path.join(os.getcwd(), "flow_outputs")
        os.makedirs(self.download_dir, exist_ok=True)
        
        self._playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def is_port_open(self, host: str = "127.0.0.1", port: int = DEFAULT_CDP_PORT) -> bool:
        """Verifica se a porta CDP está aberta e respondendo."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0

    def launch_browser_process(self, headless: bool = False):
        """Inicia o Chromium com depuração remota e perfil persistente."""
        chrome_path = find_chrome_binary()
        if not chrome_path:
            raise FileNotFoundError(
                "Google Chrome / Chromium não foi encontrado no sistema. "
                "Defina a variável de ambiente CHROME_PATH apontando para o seu executável do Chrome."
            )
            
        args = [
            chrome_path,
            f"--remote-debugging-port={DEFAULT_CDP_PORT}",
            f"--user-data-dir={self.user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            FLOW_BASE_URL
        ]
        if headless:
            args.append("--headless=new")
            
        subprocess.Popen(args)
        # Aguarda inicialização da porta
        for _ in range(15):
            time.sleep(1)
            if self.is_port_open():
                return
        raise TimeoutError("Navegador não abriu a porta de depuração a tempo.")

    def connect(self, auto_launch: bool = True) -> Page:
        """Conecta ao navegador via CDP e retorna a aba principal do Google Flow."""
        if not self.is_port_open():
            if auto_launch:
                self.launch_browser_process()
            else:
                raise ConnectionError(f"Nenhum navegador escutando em {self.cdp_url}.")
                
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.connect_over_cdp(self.cdp_url)
        self.context = self.browser.contexts[0]
        
        # Encontra aba do Google Flow
        target_page = None
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
        self.set_download_path(self.download_dir)
        return self.page

    def dismiss_modals(self):
        """Fecha modais de onboarding, novidades e anúncios."""
        if not self.page:
            return
        time.sleep(0.5)
        comecar_btn = self.page.locator("button:has-text('Começar'), button:has-text('Entendi')").first
        if comecar_btn.is_visible():
            comecar_btn.click()
            time.sleep(0.8)
        else:
            self.page.keyboard.press("Escape")

    def ensure_canvas(self):
        """Garante retorno ao canvas principal se o visualizador estiver aberto."""
        if not self.page:
            return
        concluir = self.page.locator("button:has-text('Concluir')").first
        if concluir.is_visible():
            concluir.click()
            time.sleep(1)

    def set_download_path(self, path: str):
        """Define o diretório de download nativo do Chromium via CDP."""
        self.download_dir = path
        os.makedirs(self.download_dir, exist_ok=True)
        if self.page:
            cdp = self.page.context.new_cdp_session(self.page)
            cdp.send("Page.setDownloadBehavior", {
                "behavior": "allow",
                "downloadPath": self.download_dir
            })

    def close(self):
        """Encerra a conexão cliente sem fechar o navegador."""
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
