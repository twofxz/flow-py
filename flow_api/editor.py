"""
FlowEditor - Controle do editor ProseMirror, modelos e aspect ratio.
"""

import time
from typing import Optional
from playwright.sync_api import Page

class FlowEditor:
    def __init__(self, page: Page):
        self.page = page

    def verify_and_set_settings(self, model: str = "Nano Banana 2", aspect_ratio: str = "16:9"):
        """Configura modelo e proporção no canvas com política estrita anti-lite."""
        if "lite" in model.lower():
            raise ValueError(f"Modelo proibido: {model}. O Google Flow requer Nano Banana 2 ou Nano Banana Pro.")
            
        settings_btn = self.page.locator("button[aria-label='Gatilho de configurações']").first
        if settings_btn.is_visible():
            text = settings_btn.inner_text()
            ratio_key = aspect_ratio.replace(":", "_")
            needs_model_change = model not in text
            needs_ratio_change = ratio_key not in text and aspect_ratio not in text
            
            if not needs_model_change and not needs_ratio_change:
                return
                
            self.page.keyboard.press("Escape")
            time.sleep(0.3)
            settings_btn.click()
            time.sleep(1)
            
            if needs_ratio_change:
                ratio_btn = self.page.locator(f"button:has-text('{aspect_ratio}')").first
                if ratio_btn.is_visible():
                    ratio_btn.click()
                    time.sleep(0.5)
                    
            if needs_model_change:
                model_btn = self.page.locator(f"button:has-text('{model}'), [role='option']:has-text('{model}')").first
                if model_btn.is_visible():
                    model_btn.click()
                    time.sleep(0.5)
                    
            self.page.keyboard.press("Escape")
            time.sleep(0.5)

    def submit_prompt(self, prompt: str, model: str = "Nano Banana 2", aspect_ratio: str = "16:9"):
        """Injeta prompt na caixa ProseMirror e inicia a renderização."""
        self.verify_and_set_settings(model=model, aspect_ratio=aspect_ratio)
        
        pm = self.page.locator(".ProseMirror").first
        if not pm.is_visible():
            raise RuntimeError("Editor ProseMirror não encontrado no canvas.")
            
        pm.click()
        time.sleep(0.2)
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Backspace")
        time.sleep(0.2)
        
        # Injeção no nó de texto com dispatch de input event
        pm.evaluate("(el, text) => { el.innerText = text; el.dispatchEvent(new Event('input', { bubbles: true })); }", prompt)
        pm.click()
        self.page.keyboard.press("End")
        self.page.keyboard.type(" ")
        self.page.keyboard.press("Backspace")
        time.sleep(0.4)
        
        submit_btn = self.page.locator("button[aria-label*='geração'], button[aria-label*='Iniciar'], button:has-text('arrow_forward')").first
        submit_btn.click()

    def wait_for_generation(self, timeout: int = 90) -> bool:
        """Aguarda conclusão reativa da geração."""
        start_time = time.time()
        time.sleep(4)
        while time.time() - start_time < timeout:
            state = self.page.evaluate("""() => {
                const text = document.body.innerText;
                const isGenerating = text.includes('%') || text.includes('Gerando') || text.includes('Criando') || document.querySelector('[role="progressbar"]') !== null;
                return { isGenerating: isGenerating };
            }""")
            if not state['isGenerating']:
                time.sleep(2)
                return True
            time.sleep(2)
        return False
