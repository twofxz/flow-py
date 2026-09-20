"""
FlowDownloader - Recupera ativos gerados em resolução nativa original (1K/2K).
"""

import os
import time
from typing import List, Dict, Optional
from playwright.sync_api import Page

class FlowDownloader:
    def __init__(self, page: Page, download_dir: str):
        self.page = page
        self.download_dir = download_dir

    def open_viewer(self, force_newest: bool = False):
        """Garante que o visualizador detalhado esteja aberto (seja na rota /edit/ ou via card do canvas)."""
        if "/edit/" in self.page.url:
            return

        # 1. Caso esteja no canvas principal, clica no primeiro flow-grid-tile-container no canto superior esquerdo (evita botão play)
        tile = self.page.locator("flow-grid-tile-container").first
        try:
            tile.wait_for(state="visible", timeout=8000)
            tile.click(position={"x": 20, "y": 20})
        except Exception:
            pass

        # Aguarda transição para /edit/
        try:
            self.page.wait_for_url("**/edit/**", timeout=8000)
        except Exception:
            pass

        # Aguarda botão de download estar visível
        try:
            dl_btn = self.page.locator("button[aria-label*='Baixar'], button:has-text('Baixar')").first
            dl_btn.wait_for(state="visible", timeout=8000)
        except Exception:
            pass

    def get_rail_thumbnails(self) -> List[Dict]:
        """Identifica os botões de miniaturas disponíveis na barra superior do visualizador."""
        self.open_viewer()
        buttons = self.page.locator(".rail-container button").all()
        targets = []
        for btn in buttons:
            aria = btn.get_attribute("aria-label") or ""
            if aria and not any(nav in aria.lower() for nav in ["anterior", "próxima", "proxima"]):
                targets.append({"element": btn, "aria": aria})
        return targets

    def download_current(self, resolution: str = "1K", filename: Optional[str] = None, timeout: int = 25) -> Optional[str]:
        """Baixa a mídia ativa na tela na resolução nativa especificada com fallback inteligente."""
        default_downloads = os.path.expanduser(r"~\Downloads")
        before_custom = set(os.listdir(self.download_dir)) if os.path.exists(self.download_dir) else set()
        before_default = set(os.listdir(default_downloads)) if os.path.exists(default_downloads) else set()

        # 1. Clica no botão 'Baixar mídia' se o menu não estiver aberto
        menu_open = self.page.evaluate("""() => {
            const btn = document.querySelector("button[aria-label*='Baixar'], button:has-text('Baixar')");
            return btn && btn.getAttribute('aria-expanded') === 'true';
        }""")

        if not menu_open:
            dl_btn = self.page.locator("button[aria-label*='Baixar'], button:has-text('Baixar')").first
            try:
                if dl_btn.is_visible():
                    dl_btn.click(force=True)
                else:
                    self.page.evaluate("""() => {
                        const btn = Array.from(document.querySelectorAll('button')).find(b => 
                            b.innerText.includes('Baixar') || b.getAttribute('aria-label')?.includes('Baixar')
                        );
                        if (btn) btn.click();
                    }""")
            except Exception:
                pass
            time.sleep(0.8)

        # 2. Localiza item de menu da resolução desejada
        item_btn = self.page.locator(".cdk-overlay-container button, .cdk-overlay-container [role='menuitem']").filter(has_text=resolution).first
        if not item_btn.is_visible():
            item_btn = self.page.locator(".cdk-overlay-container button, .cdk-overlay-container [role='menuitem']").filter(has_text="1K").first
        if not item_btn.is_visible():
            item_btn = self.page.locator(".cdk-overlay-container button, .cdk-overlay-container [role='menuitem']").filter(has_text="Original").first

        # 3. Tenta download com expect_download nativo do Playwright
        download_obj = None
        try:
            with self.page.expect_download(timeout=5000) as dl_info:
                if item_btn.is_visible():
                    item_btn.click()
                else:
                    self.page.evaluate("""(res) => {
                        const menuItems = Array.from(document.querySelectorAll('[role="menuitem"], .mat-mdc-menu-item, button'));
                        const target = menuItems.find(m => m.innerText && (m.innerText.includes(res) || m.innerText.includes('Original') || m.innerText.includes('1K')));
                        if (target) target.click();
                    }""", resolution)
            download_obj = dl_info.value
        except Exception:
            try:
                if item_btn.is_visible():
                    item_btn.click(force=True)
            except Exception:
                pass

        if download_obj:
            try:
                suggested = download_obj.suggested_filename or "image.jpeg"
                target_name = filename or suggested
                dest = os.path.join(self.download_dir, target_name)
                os.makedirs(self.download_dir, exist_ok=True)
                if os.path.exists(dest):
                    os.remove(dest)
                download_obj.save_as(dest)
                print(f"[FlowDownloader] Arquivo baixado via CDP: {target_name} ({os.path.getsize(dest)} bytes)")
                self.page.keyboard.press("Escape")
                return dest
            except Exception:
                pass

        # 4. Monitora diretamente a pasta de download (caso Page.setDownloadBehavior tenha salvado no disco)
        for _ in range(timeout):
            time.sleep(1)
            if os.path.exists(self.download_dir):
                after_custom = set(os.listdir(self.download_dir))
                diff_custom = after_custom - before_custom
                new_imgs = [f for f in diff_custom if f.lower().endswith(('.jpeg', '.jpg', '.png', '.webp')) and not f.endswith('.crdownload')]
                if new_imgs:
                    full_path = os.path.join(self.download_dir, new_imgs[0])
                    if filename:
                        target_path = os.path.join(self.download_dir, filename)
                        if os.path.exists(target_path):
                            os.remove(target_path)
                        os.rename(full_path, target_path)
                        full_path = target_path
                    print(f"[FlowDownloader] Arquivo capturado no disco: {os.path.basename(full_path)} ({os.path.getsize(full_path)} bytes)")
                    self.page.keyboard.press("Escape")
                    return full_path

            if os.path.exists(default_downloads):
                after_default = set(os.listdir(default_downloads))
                diff_default = after_default - before_default
                new_imgs_def = [f for f in diff_default if f.lower().endswith(('.jpeg', '.jpg', '.png', '.webp')) and not f.endswith('.crdownload')]
                if new_imgs_def:
                    src = os.path.join(default_downloads, new_imgs_def[0])
                    target_name = filename or new_imgs_def[0]
                    dest = os.path.join(self.download_dir, target_name)
                    import shutil
                    if os.path.exists(dest):
                        os.remove(dest)
                    shutil.move(src, dest)
                    print(f"[FlowDownloader] Arquivo capturado em Downloads e movido: {target_name} ({os.path.getsize(dest)} bytes)")
                    self.page.keyboard.press("Escape")
                    return dest

        self.page.keyboard.press("Escape")
        return None

    def download_all_rail(self, resolution: str = "1K", max_items: Optional[int] = None) -> List[str]:
        """Percorre a barra de miniaturas e baixa todos os ativos originais."""
        thumbnails = self.get_rail_thumbnails()
        if max_items:
            thumbnails = thumbnails[:max_items]
            
        downloaded_paths = []
        print(f"[FlowDownloader] Iniciando download de {len(thumbnails)} ativos em {resolution}...")
        
        for idx, thumb in enumerate(thumbnails):
            print(f"[FlowDownloader] [{idx+1}/{len(thumbnails)}] Selecionando '{thumb['aria']}'...")
            thumb['element'].click()
            time.sleep(1.2)
            
            path = self.download_current(resolution=resolution)
            if path:
                downloaded_paths.append(path)
            time.sleep(1)
            
        return downloaded_paths

    def download_video(self, resolution: str = "720p", filename: Optional[str] = None, timeout: int = 40) -> Optional[str]:
        """Baixa o vídeo ativo no visualizador no formato nativo MP4 com detecção dual (CDP e disco)."""
        self.open_viewer()

        target_name = filename
        print(f"[FlowDownloader] Selecionando resolução {resolution}...")

        dl_btn = self.page.locator("button[aria-label*='Baixar mídia'], button[aria-label*='Baixar']").first
        try:
            dl_btn.wait_for(state="visible", timeout=8000)
        except Exception:
            self.open_viewer()

        for attempt in range(1, 4):
            if attempt > 1:
                print(f"[FlowDownloader] Tentativa {attempt}/3 de download do vídeo em {resolution}...")
                self.page.keyboard.press("Escape")
                time.sleep(1.0)
                self.open_viewer()

            before_files = set(os.listdir(self.download_dir)) if os.path.exists(self.download_dir) else set()

            # 1. Verifica se menu de download já está aberto
            menu_open = self.page.evaluate("""() => {
                const btn = document.querySelector("button[aria-label*='Baixar mídia'], button[aria-label*='Baixar']");
                return btn && btn.getAttribute('aria-expanded') === 'true';
            }""")

            if not menu_open:
                dl_btn = self.page.locator("button[aria-label*='Baixar mídia'], button[aria-label*='Baixar']").first
                try:
                    dl_btn.click(force=True)
                except Exception:
                    self.page.evaluate("""() => {
                        const btn = document.querySelector("button[aria-label*='Baixar mídia'], button[aria-label*='Baixar']");
                        if (btn) btn.click();
                    }""")

            # 2. Localiza e aguarda o botão da resolução no overlay
            item_btn = self.page.locator(".cdk-overlay-container button").filter(has_text=resolution).first
            try:
                item_btn.wait_for(state="visible", timeout=4000)
            except Exception:
                item_btn = self.page.locator(".cdk-overlay-container button").filter(has_text="720p").first

            # 3. Dispara o clique com captura dual
            download_obj = None
            try:
                with self.page.expect_download(timeout=5000) as dl_info:
                    item_btn.click()
                download_obj = dl_info.value
            except Exception:
                try:
                    item_btn.click(force=True)
                except Exception:
                    pass

            # Caso A: Capturado via Playwright expect_download
            if download_obj:
                suggested = download_obj.suggested_filename or "video.mp4"
                final_name = target_name or suggested
                if not any(final_name.lower().endswith(ext) for ext in ['.mp4', '.mov', '.webm']):
                    ext = os.path.splitext(suggested)[1] or '.mp4'
                    final_name = f"{final_name}{ext}"
                dest = os.path.join(self.download_dir, final_name)
                os.makedirs(self.download_dir, exist_ok=True)

                try:
                    temp_path = download_obj.path()
                    if temp_path and os.path.exists(temp_path):
                        import shutil
                        if os.path.exists(dest):
                            os.remove(dest)
                        shutil.copy2(temp_path, dest)
                        size = os.path.getsize(dest)
                        if size > 50000:
                            print(f"[FlowDownloader] Vídeo baixado com sucesso via CDP: {final_name} ({size} bytes)")
                            self.page.keyboard.press("Escape")
                            return dest
                except Exception as e:
                    print(f"[FlowDownloader] Erro ao salvar arquivo via CDP: {e}")

            # Caso B: Capturado diretamente no disco (Page.setDownloadBehavior nativo do Chrome)
            for _ in range(15):
                time.sleep(1)
                after_files = set(os.listdir(self.download_dir)) if os.path.exists(self.download_dir) else set()
                diff = after_files - before_files
                new_vids = [f for f in diff if f.lower().endswith(('.mp4', '.mov', '.webm')) and not f.endswith('.crdownload')]
                if new_vids:
                    downloaded = new_vids[0]
                    full_path = os.path.join(self.download_dir, downloaded)
                    size = os.path.getsize(full_path)
                    if size > 50000:
                        if target_name:
                            final_name = target_name
                            if not any(final_name.lower().endswith(ext) for ext in ['.mp4', '.mov', '.webm']):
                                final_name = f"{final_name}.mp4"
                            dest = os.path.join(self.download_dir, final_name)
                            if os.path.exists(dest):
                                os.remove(dest)
                            os.rename(full_path, dest)
                            full_path = dest
                            downloaded = final_name
                        print(f"[FlowDownloader] Vídeo salvo com sucesso no disco: {downloaded} ({size} bytes)")
                        self.page.keyboard.press("Escape")
                        return full_path

            time.sleep(attempt * 2)

        self.page.keyboard.press("Escape")
        return None

    def download_batch(self, count: int, filenames: Optional[List[str]] = None, resolution: str = "1K", timeout: int = 25) -> List[str]:
        """Baixa deterministamente os últimos `count` ativos gerados em lote na ordem correta (Slide 1 a N)."""
        # Garante retorno ao canvas
        self.page.keyboard.press("Escape")
        time.sleep(0.5)
        back_btn = self.page.locator("button[aria-label*='Voltar'], button[aria-label*='voltar']").first
        if back_btn.is_visible():
            back_btn.click()
            time.sleep(1)

        # Identifica contêineres de cards no canvas via JS
        tiles_count = self.page.evaluate("""() => {
            const tiles = document.querySelectorAll('flow-grid-tile-container');
            return tiles.length;
        }""")

        print(f"[FlowDownloader] Total de {tiles_count} cards identificados no canvas.")
        variations = 2 if tiles_count >= 2 * count else 1
        if variations == 2:
            print(f"[FlowDownloader] Detectado modo 'x2' do Flow ({tiles_count} cards para {count} slides). Mapeando variação principal de cada slide.")

        downloaded_paths = []
        for idx in range(count):
            custom_name = filenames[idx] if filenames and idx < len(filenames) else f"slide_{idx+1:02d}.jpeg"
            card_idx = (count - 1 - idx) * variations
            print(f"[FlowDownloader] [{idx+1}/{count}] Abrindo card do Slide {idx+1} (card #{card_idx}) para salvar como '{custom_name}'...")
            try:
                # Clica no container do card via JS
                clicked = self.page.evaluate("""(idx) => {
                    const tiles = document.querySelectorAll('flow-grid-tile-container');
                    if (tiles[idx]) {
                        tiles[idx].click();
                        return true;
                    }
                    return false;
                }""", card_idx)

                if not clicked:
                    imgs = self.page.locator("flow-grid-tile-container, img:not(.ghost-image)").all()
                    if card_idx < len(imgs):
                        imgs[card_idx].click(force=True)

                time.sleep(1.8)
                saved_path = self.download_current(resolution=resolution, filename=custom_name, timeout=timeout)
                if saved_path:
                    downloaded_paths.append(saved_path)
                else:
                    print(f"[FlowDownloader] Falha ao baixar Slide {idx+1} ('{custom_name}').")

                # Retorna ao canvas para o próximo card
                self.page.keyboard.press("Escape")
                time.sleep(0.5)
                back = self.page.locator("button[aria-label*='Voltar'], button[aria-label*='voltar']").first
                if back.is_visible():
                    back.click(force=True)
                time.sleep(0.8)
            except Exception as e:
                print(f"[FlowDownloader] Erro ao processar Slide {idx+1}: {e}")
                self.page.keyboard.press("Escape")
                time.sleep(1.0)

        print(f"[FlowDownloader] Concluído download de {len(downloaded_paths)}/{count} arquivos do lote com ordem determinística garantida!")
        return downloaded_paths

