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

    def open_viewer(self):
        """Abre o visualizador detalhado a partir do card mais recente do canvas."""
        if self.page.locator("button[aria-label='Baixar mídia']").is_visible() or self.page.locator(".rail-container").is_visible():
            return
            
        img = self.page.locator("img:not(.ghost-image)").all()
        for i in reversed(img):
            box = i.bounding_box()
            if box and box['width'] > 200 and box['height'] > 150:
                try:
                    i.scroll_into_view_if_needed()
                    i.click(force=True)
                    time.sleep(2)
                    if self.page.locator("button[aria-label='Baixar mídia']").is_visible():
                        break
                except Exception:
                    continue

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

        # 1. Clica no botão 'Baixar mídia' via JS injetado
        clicked = self.page.evaluate("""() => {
            const dlBtn = Array.from(document.querySelectorAll('button')).find(b => 
                b.innerText.includes('Baixar') || b.getAttribute('aria-label')?.includes('Baixar')
            );
            if (!dlBtn) return false;
            dlBtn.click();
            return true;
        }""")
        
        if not clicked:
            print("[FlowDownloader] Botão de download não visível na tela.")
            return None

        time.sleep(0.8)

        # 2. Clica no item de resolução (1K / 2K) via JS
        res_clicked = self.page.evaluate("""(res) => {
            const menuItems = Array.from(document.querySelectorAll('[role="menuitem"], .mat-mdc-menu-item, button, span'));
            const target = menuItems.find(m => m.innerText && m.innerText.includes(res));
            if (target) {
                target.click();
                return true;
            }
            const original = menuItems.find(m => m.innerText && (m.innerText.includes('Original') || m.innerText.includes('1K') || m.innerText.includes('2K')));
            if (original) {
                original.click();
                return true;
            }
            return false;
        }""", resolution)

        if not res_clicked:
            print(f"[FlowDownloader] Resolução {resolution} não encontrada no menu.")
            self.page.keyboard.press("Escape")
            return None

        # 3. Aguarda o arquivo aparecer na pasta (customizada ou padrão ~/Downloads)
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
                    print(f"[FlowDownloader] Arquivo baixado: {os.path.basename(full_path)} ({os.path.getsize(full_path)} bytes)")
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
                    print(f"[FlowDownloader] Arquivo capturado e movido: {target_name} ({os.path.getsize(dest)} bytes)")
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

    def download_video(self, resolution: str = "720p", filename: Optional[str] = None, timeout: int = 15) -> Optional[str]:
        """Baixa o vídeo ativo no visualizador no formato nativo MP4."""
        self.open_viewer()
        dl_btn = self.page.locator("button[aria-label='Baixar mídia']").first
        if not dl_btn.is_visible():
            print("[FlowDownloader] Botão de download de vídeo não visível.")
            return None
            
        dl_btn.click()
        time.sleep(0.8)
        
        # Opção de resolução (ex: 720p)
        res_btn = self.page.locator(f"text='{resolution}'").first
        if not res_btn.is_visible():
            res_btn = self.page.locator(f"flow-menu-item button:has-text('{resolution}')").first
        if not res_btn.is_visible():
            res_btn = self.page.locator("flow-menu-item button, [role='menuitem']").first
            
        before_files = set(os.listdir(self.download_dir))
        default_downloads = os.path.expanduser(r"~\Downloads")
        before_default = set(os.listdir(default_downloads))
        
        print(f"[FlowDownloader] Opção {resolution} encontrada! Clicando...")
        try:
            with self.page.expect_download(timeout=8000) as download_info:
                res_btn.click(force=True)
            download = download_info.value
            target_name = filename or f"flow_video_{int(time.time())}.mp4"
            if not target_name.lower().endswith(('.mp4', '.mov', '.webm')):
                target_name = f"{target_name}.mp4"
            target_path = os.path.join(self.download_dir, target_name)
            download.save_as(target_path)
            self.page.keyboard.press("Escape")
            print(f"[FlowDownloader] Vídeo baixado com sucesso: {target_name} ({os.path.getsize(target_path)} bytes)")
            return target_path
        except Exception as err:
            print(f"[FlowDownloader] Interceptador de download seguiu via sistema de arquivos: {err}")
            res_btn.click(force=True)
        
        for _ in range(timeout):
            time.sleep(1)
            after_files = set(os.listdir(self.download_dir))
            diff = after_files - before_files
            new_vids = [f for f in diff if f.endswith(('.mp4', '.mov', '.webm')) and not f.endswith('.crdownload')]
            if new_vids:
                downloaded = new_vids[0]
                full_path = os.path.join(self.download_dir, downloaded)
                
                if filename:
                    if not any(filename.lower().endswith(ext) for ext in ['.mp4', '.mov', '.webm']):
                        ext = os.path.splitext(downloaded)[1] or '.mp4'
                        filename = f"{filename}{ext}"
                    target_path = os.path.join(self.download_dir, filename)
                    if os.path.exists(target_path):
                        os.remove(target_path)
                    os.rename(full_path, target_path)
                    full_path = target_path
                    downloaded = filename
                    
                print(f"[FlowDownloader] Vídeo baixado com sucesso: {downloaded} ({os.path.getsize(full_path)} bytes)")
                self.page.keyboard.press("Escape")
                return full_path
                
            after_default = set(os.listdir(default_downloads))
            diff_def = after_default - before_default
            new_vids_def = [f for f in diff_def if f.endswith(('.mp4', '.mov', '.webm')) and not f.endswith('.crdownload')]
            if new_vids_def:
                src = os.path.join(default_downloads, new_vids_def[0])
                target_name = filename or new_vids_def[0]
                if not target_name.lower().endswith(('.mp4', '.mov', '.webm')):
                    target_name = f"{target_name}.mp4"
                dest = os.path.join(self.download_dir, target_name)
                import shutil
                shutil.move(src, dest)
                print(f"[FlowDownloader] Vídeo movido com sucesso: {target_name} ({os.path.getsize(dest)} bytes)")
                self.page.keyboard.press("Escape")
                return dest
                
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

