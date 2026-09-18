"""
FlowDownloader - Download nativo em resolução original (1K / 2K) sem perda de qualidade.
"""

import os
import time
from typing import Optional
from playwright.sync_api import Page

class FlowDownloader:
    def __init__(self, page: Page, download_dir: str):
        self.page = page
        self.download_dir = download_dir

    def open_viewer(self):
        """Abre o visualizador na primeira mídia."""
        if self.page.locator(".rail-container").is_visible():
            return
        imgs = self.page.locator("img").all()
        for i in imgs:
            box = i.bounding_box()
            if box and box['width'] > 200 and box['height'] > 150:
                i.click()
                time.sleep(1.5)
                break

    def download_current(self, resolution: str = "1K", timeout: int = 10) -> Optional[str]:
        """Baixa o ativo atualmente visível no visualizador na resolução desejada."""
        self.open_viewer()
        dl_btn = self.page.locator("button[aria-label='Baixar mídia']").first
        if not dl_btn.is_visible():
            return None
            
        dl_btn.click()
        time.sleep(0.8)
        
        res_btn = self.page.locator(f"flow-menu-item button:has-text('{resolution}')").first
        if not res_btn.is_visible():
            self.page.keyboard.press("Escape")
            return None
            
        before_files = set(os.listdir(self.download_dir))
        res_btn.click()
        
        for _ in range(timeout):
            time.sleep(1)
            after_files = set(os.listdir(self.download_dir))
            diff = after_files - before_files
            new_imgs = [f for f in diff if f.endswith(('.jpeg', '.jpg', '.png')) and not f.endswith('.crdownload')]
            if new_imgs:
                return os.path.join(self.download_dir, new_imgs[0])
                
        return None
