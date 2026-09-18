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
        """Abre o visualizador detalhado a partir do primeiro card de imagem do canvas."""
        if self.page.locator(".rail-container").is_visible():
            return
            
        img = self.page.locator("img").all()
        for i in img:
            box = i.bounding_box()
            if box and box['width'] > 200 and box['height'] > 150:
                i.click()
                time.sleep(2)
                break

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

    def download_current(self, resolution: str = "1K", filename: Optional[str] = None, timeout: int = 12) -> Optional[str]:
        """Baixa a mídia ativa na tela na resolução nativa especificada."""
        dl_btn = self.page.locator("button[aria-label='Baixar mídia']").first
        if not dl_btn.is_visible():
            print("[FlowDownloader] Botão de download não visível na tela.")
            return None
            
        dl_btn.click()
        time.sleep(0.8)
        
        # Localiza o botão exato da resolução no menu
        res_btn = self.page.locator(f"flow-menu-item button:has-text('{resolution}')").first
        if not res_btn.is_visible():
            print(f"[FlowDownloader] Resolução {resolution} não encontrada no menu.")
            self.page.keyboard.press("Escape")
            return None
            
        before_files = set(os.listdir(self.download_dir))
        res_btn.click()
        
        # Aguarda o arquivo aparecer na pasta
        for _ in range(timeout):
            time.sleep(1)
            after_files = set(os.listdir(self.download_dir))
            diff = after_files - before_files
            new_imgs = [f for f in diff if f.endswith(('.jpeg', '.jpg', '.png')) and not f.endswith('.crdownload')]
            if new_imgs:
                downloaded = new_imgs[0]
                full_path = os.path.join(self.download_dir, downloaded)
                
                if filename:
                    if not any(filename.lower().endswith(ext) for ext in ['.jpeg', '.jpg', '.png', '.webp']):
                        ext = os.path.splitext(downloaded)[1]
                        filename = f"{filename}{ext}"
                    target_path = os.path.join(self.download_dir, filename)
                    if os.path.exists(target_path):
                        os.remove(target_path)
                    os.rename(full_path, target_path)
                    full_path = target_path
                    downloaded = filename
                    
                print(f"[FlowDownloader] Arquivo baixado: {downloaded} ({os.path.getsize(full_path)} bytes)")
                return full_path
                
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
