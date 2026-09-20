"""
FlowClient - Gerencia conexão CDP, perfil persistente e abas ativas do Google Flow.
"""

import os
import time
import socket
import subprocess
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

import sys
import shutil

DEFAULT_CDP_URL = "http://127.0.0.1:9222"
FLOW_HOME = os.environ.get("FLOW_HOME", os.path.expanduser("~/.google-flow"))
DEFAULT_PROFILE = os.path.join(FLOW_HOME, "profile")
FLOW_BASE_URL = "https://flow.google.com"

def find_chrome_executable() -> str:
    """Localiza automaticamente o executável do Google Chrome ou Chromium no sistema (Windows, macOS, Linux)."""
    # 1. Variável de ambiente explícita
    env_bin = os.environ.get("FLOW_CHROME_BIN") or os.environ.get("CHROME_PATH")
    if env_bin and os.path.exists(env_bin):
        return env_bin

    # 2. Caminhos específicos por plataforma
    candidates = []
    if os.name == 'nt':
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        user_profile = os.environ.get("USERPROFILE", "")

        candidates = [
            # Instalação portátil ou local se configurada
            os.path.join(user_profile, r"chrome\win64-153.0.8010.47\chrome-win64\chrome.exe"),
            # Google Chrome padrão
            os.path.join(program_files, r"Google\Chrome\Application\chrome.exe"),
            os.path.join(program_files_x86, r"Google\Chrome\Application\chrome.exe"),
            os.path.join(local_app_data, r"Google\Chrome\Application\chrome.exe"),
            # Brave Browser
            os.path.join(program_files, r"BraveSoftware\Brave-Browser\Application\brave.exe"),
            os.path.join(local_app_data, r"BraveSoftware\Brave-Browser\Application\brave.exe"),
            # Microsoft Edge
            os.path.join(program_files, r"Microsoft\Edge\Application\msedge.exe"),
            os.path.join(program_files_x86, r"Microsoft\Edge\Application\msedge.exe"),
        ]
    elif sys.platform == 'darwin':
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
        ]
    else:  # Linux
        for binary_name in ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium", "brave-browser"]:
            path = shutil.which(binary_name)
            if path:
                return path

    for path in candidates:
        if path and os.path.exists(path):
            return path

    # 3. Fallback: procurar no PATH do sistema
    for bin_name in ["chrome", "chrome.exe", "chromium", "chromium.exe", "msedge", "msedge.exe"]:
        path = shutil.which(bin_name)
        if path:
            return path

    raise FileNotFoundError(
        "Nenhum executável do Chrome/Chromium encontrado no sistema. "
        "Por favor, instale o Google Chrome ou defina a variável de ambiente FLOW_CHROME_BIN com o caminho completo do executável."
    )

def detect_session(session: Optional[str] = None) -> str:
    """Detecta automaticamente o agente de IA ou usa a sessão fornecida."""
    if session:
        return session.lower().strip()
    if os.environ.get("ANTIGRAVITY_AGENT"):
        return "antigravity"
    if os.environ.get("CODEX") or os.environ.get("CODEX_THREAD_ID"):
        return "codex"
    return "default"

class FlowClient:
    def __init__(self, cdp_url: str = DEFAULT_CDP_URL, download_dir: Optional[str] = None, session: Optional[str] = None, headless: bool = True):
        self.cdp_url = cdp_url
        self.download_dir = download_dir or os.environ.get("FLOW_DOWNLOAD_DIR", os.path.expanduser(r"~\Downloads\google_flow_assets"))
        os.makedirs(self.download_dir, exist_ok=True)
        self.session = detect_session(session)
        self.headless = headless
        
        self._playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
    def start_browser_if_needed(self):
        """Verifica a porta 9222 e inicia o Chromium persistente de forma cross-platform se necessário."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 9222))
        sock.close()
        
        if result != 0:
            chrome_bin = find_chrome_executable()
            mode_desc = "HEADLESS (invisível)" if self.headless else "VISIBLE (com janela)"
            print(f"[FlowClient] Navegador não detectado na porta 9222. Iniciando processo persistente em modo {mode_desc} ({chrome_bin})...")
            
            flags = [
                '--remote-debugging-port=9222',
                f'--user-data-dir="{DEFAULT_PROFILE}"',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--window-size=1920,1080'
            ]
            if self.headless:
                flags.extend([
                    '--headless=new',
                    '--enable-gpu',
                    '--use-gl=angle'
                ])

            if os.name == 'nt':
                # Usa WMI (Win32_Process) no Windows para desacoplar totalmente do Job Object do terminal
                flags_str = " ".join(flags)
                cmd_line = f'"{chrome_bin}" {flags_str} "{FLOW_BASE_URL}"'
                ps_script = f"Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{{CommandLine = '{cmd_line}'}}"
                subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True)
            else:
                cmd = [chrome_bin] + [f.strip('"') for f in flags] + [FLOW_BASE_URL]
                subprocess.Popen(cmd, start_new_session=True, close_fds=True)
            time.sleep(3)

    def get_cached_project_url(self) -> Optional[str]:
        """Recupera o último projeto ativo da sessão para evitar criar projetos novos em branco."""
        cache_file = os.path.join(DEFAULT_PROFILE, f"active_project_{self.session}.json")
        if not os.path.exists(cache_file):
            cache_file = os.path.join(DEFAULT_PROFILE, "active_project.json")
        if os.path.exists(cache_file):
            try:
                import json
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("project_url")
            except Exception:
                pass
        return None

    def save_cached_project_url(self, url: str):
        """Salva a URL do projeto ativo no cache específico da sessão."""
        if "flow.google.com/project/" not in url:
            return
        cache_file = os.path.join(DEFAULT_PROFILE, f"active_project_{self.session}.json")
        try:
            import json
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump({"project_url": url, "updated_at": time.time(), "session": self.session}, f)
        except Exception:
            pass

    def is_tab_busy(self, page: Page) -> bool:
        """Verifica de forma ultra-rápida se a aba já está executando uma geração ou automação."""
        try:
            # 1. Verifica flag em memória JS da página
            busy_flag = page.evaluate("""() => {
                if (window.__flow_busy__) {
                    // Se o lock tiver mais de 5 minutos, considera travamento zumbi e libera
                    if (Date.now() - (window.__flow_busy_at__ || 0) > 300000) {
                        window.__flow_busy__ = false;
                        return false;
                    }
                    return true;
                }
                return false;
            }""")
            if busy_flag:
                return True

            # 2. Verifica se o Google Flow tem barra de progresso ou botão cancelar ativo no DOM
            if page.locator("button:has-text('Cancelar'), [role='progressbar']").count() > 0:
                return True

            return False
        except Exception:
            return False

    def mark_tab_busy(self, busy: bool = True):
        """Marca ou desmarca a aba ativa como ocupada/livre no contexto do navegador."""
        if not self.page:
            return
        try:
            self.page.evaluate("""([busy, sess]) => {
                window.__flow_busy__ = busy;
                window.__flow_busy_at__ = busy ? Date.now() : 0;
                if (busy) {
                    window.__flow_session__ = sess;
                }
            }""", [busy, self.session])
        except Exception:
            pass

    def connect(self) -> Page:
        """Conecta ao Chromium via CDP e sincroniza ou acessa uma aba exclusiva e livre."""
        self.start_browser_if_needed()
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.connect_over_cdp(self.cdp_url)
        self.context = self.browser.contexts[0]

        target_page = None
        cached_url = self.get_cached_project_url()

        # Estratégia 1: Procura se já existe uma aba associada a esta sessão específica e que NÃO esteja ocupada
        for page in self.context.pages:
            if "flow.google.com" in page.url:
                try:
                    page_session = page.evaluate("() => window.__flow_session__ || ''")
                    if page_session == self.session and not self.is_tab_busy(page):
                        target_page = page
                        print(f"[FlowClient] Conectado à aba dedicada existente da sessão '{self.session}'.")
                        break
                except Exception:
                    pass

        # Estratégia 2: Se temos uma URL em cache para esta sessão, tenta achar aba com essa URL que esteja livre
        if not target_page and cached_url:
            for page in self.context.pages:
                if cached_url in page.url and not self.is_tab_busy(page):
                    target_page = page
                    print(f"[FlowClient] Conectado à aba com o projeto da sessão: {page.url}")
                    break

        # Estratégia 3: Procura QUALQUER aba existente de projeto no Flow que esteja LIVRE (não ocupada)
        if not target_page:
            for page in self.context.pages:
                if "flow.google.com/project" in page.url and not self.is_tab_busy(page):
                    target_page = page
                    print(f"[FlowClient] Acessando outra aba livre existente no navegador: {page.url}")
                    break

        # Estratégia 4: Procura aba na home do flow.google.com que esteja livre
        if not target_page:
            for page in self.context.pages:
                if "flow.google.com" in page.url and not self.is_tab_busy(page):
                    target_page = page
                    print(f"[FlowClient] Conectado à aba do Google Flow livre.")
                    break

        # Estratégia 5: Se TODAS as abas estiverem ocupadas ou nenhuma existir, abre nova aba imediatamente
        if not target_page:
            print(f"[FlowClient] Nenhuma aba livre detectada. Criando nova aba ultra-rápida para '{self.session}'...")
            target_page = self.context.new_page()
            target_url = cached_url if cached_url else FLOW_BASE_URL
            target_page.goto(target_url, wait_until="domcontentloaded")
            time.sleep(1.5)

        self.page = target_page
        try:
            self.page.set_viewport_size({"width": 1920, "height": 1080})
        except Exception:
            pass
        if not self.headless:
            try:
                self.page.bring_to_front()
            except Exception:
                pass
        self.dismiss_modals()

        # Se estiver na página inicial do Flow e não em um projeto, clica em Novo Projeto
        if "flow.google.com/project" not in self.page.url:
            new_btn = self.page.locator("button:has-text('Novo projeto'), [aria-label*='Novo projeto']").first
            if new_btn.is_visible():
                print(f"[FlowClient] Abrindo novo projeto no Flow para '{self.session}'...")
                new_btn.click()
                time.sleep(2.0)
                self.dismiss_modals()

        if "flow.google.com/project" in self.page.url:
            self.save_cached_project_url(self.page.url)

        self.mark_tab_busy(True)
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
        done_btn = self.page.locator("button[aria-label='Edição concluída'], button:has-text('check'), button:has-text('Concluir')").first
        if done_btn.is_visible():
            done_btn.click()
            time.sleep(1.5)
        else:
            self.page.keyboard.press("Escape")
            time.sleep(0.5)

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

    def check_auth_status(self) -> dict:
        """Verifica se o navegador está ativo e se a sessão do Google Flow está autenticada."""
        try:
            if not self.page:
                self.connect()
            if not self.page:
                return {"authenticated": False, "status": "disconnected", "error": "Página não conectada"}
            
            url = self.page.url
            if "accounts.google.com" in url or "signin" in url:
                return {
                    "authenticated": False,
                    "status": "auth_required",
                    "url": url,
                    "message": "Login necessário com a conta Google."
                }
            
            needs_login = self.page.evaluate("""() => {
                const text = document.body.innerText;
                return text.includes('Fazer login') || text.includes('Sign in');
            }""")
            if needs_login:
                return {
                    "authenticated": False,
                    "status": "auth_required",
                    "url": url,
                    "message": "Faça login com sua conta Google na janela aberta."
                }
            
            return {
                "authenticated": True,
                "status": "ready",
                "url": url,
                "session": self.session,
                "profile_dir": DEFAULT_PROFILE
            }
        except Exception as e:
            return {
                "authenticated": False,
                "status": "error",
                "error": str(e)
            }

    def close(self):
        """Libera o lock da aba e finaliza a sessão Playwright mantendo o Chromium aberto."""
        try:
            self.mark_tab_busy(False)
        except Exception:
            pass
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def stop_background_process(self) -> bool:
        """Encerra com segurança instâncias do Chromium em background associadas à porta 9222 ou perfil do Flow."""
        self.close()
        stopped = False
        if os.name == 'nt':
            ps_script = (
                "$procs = Get-CimInstance Win32_Process -Filter \"Name = 'chrome.exe'\" | "
                "Where-Object { $_.CommandLine -like '*remote-debugging-port=9222*' -or $_.CommandLine -like '*.google-flow*' }; "
                "foreach ($p in $procs) { Stop-Process -Id $p.ProcessId -Force; Write-Host 'Stopped PID' $p.ProcessId }"
            )
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True)
            if "Stopped PID" in (res.stdout or ""):
                stopped = True
        else:
            res = subprocess.run(["pkill", "-f", "remote-debugging-port=9222"], capture_output=True)
            stopped = (res.returncode == 0)
        return stopped
