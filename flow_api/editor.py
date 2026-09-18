import os
import time
from typing import Optional
from playwright.sync_api import Page

# Política Estrita de Modelos da Skill:
# Permitidos: 'Nano Banana 2', 'Nano Banana Pro', 'Veo 2'
# Proibidos: 'Nano Banana 2 Lite' (baixa fidelidade)
ALLOWED_IMAGE_MODELS = ["Nano Banana 2", "Nano Banana Pro"]

class FlowEditor:
    def __init__(self, page: Page):
        self.page = page

    def verify_and_set_settings(self, model: str = "Nano Banana 2", aspect_ratio: str = "16:9"):
        """Garante que o modelo e o aspect ratio configurados sigam a política estrita."""
        if "lite" in model.lower():
            raise ValueError(f"Modelo proibido: {model}. A skill requer Nano Banana 2 ou Nano Banana Pro.")
            
        settings_btn = self.page.locator("button[aria-label='Gatilho de configurações']").first
        if settings_btn.is_visible():
            text = settings_btn.inner_text()
            print(f"[FlowEditor] Configurações ativas no canvas: {repr(text)}")
            
            # Formata chave de busca do ratio (ex: 9:16 -> crop_9_16)
            ratio_key = aspect_ratio.replace(":", "_")
            needs_model_change = model not in text
            needs_ratio_change = ratio_key not in text and aspect_ratio not in text
            
            if not needs_model_change and not needs_ratio_change:
                return
                
            # Abre popover
            self.page.keyboard.press("Escape")
            time.sleep(0.3)
            settings_btn.click()
            time.sleep(1)
            
            # Altera ratio se necessário
            if needs_ratio_change:
                ratio_btn = self.page.locator(f"button:has-text('{aspect_ratio}')").first
                if ratio_btn.is_visible():
                    ratio_btn.click()
                    time.sleep(0.5)
                    print(f"[FlowEditor] Proporção alterada para {aspect_ratio}")
                    
            # Altera modelo se necessário
            if needs_model_change:
                model_btn = self.page.locator(f"button:has-text('{model}'), [role='option']:has-text('{model}')").first
                if model_btn.is_visible():
                    model_btn.click()
                    time.sleep(0.5)
                    print(f"[FlowEditor] Modelo alterado para {model}")
                    
            self.page.keyboard.press("Escape")
            time.sleep(0.5)

    def upload_reference_image(self, image_path: str) -> str:
        """Faz upload nativo de uma imagem local para o projeto Google Flow e aguarda o término do processamento."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Arquivo de imagem local não encontrado: {image_path}")
            
        filename = os.path.basename(image_path)
        self.page.keyboard.press("Escape")
        time.sleep(0.3)
        
        # 1. Clica no botão '+' do topo (Adicionar mídia)
        add_btn = self.page.locator("button[aria-label='Menu para adicionar arquivos'], button:has-text('add')").first
        if not add_btn.is_visible():
            raise RuntimeError("Botão de adicionar mídia (+) não encontrado no topo do canvas!")
        add_btn.click()
        time.sleep(0.8)
        
        # 2. Intercepta o seletor de arquivos ao clicar em 'Enviar'
        enviar_btn = self.page.locator("text='Enviar'").first
        if not enviar_btn.is_visible():
            raise RuntimeError("Opção 'Enviar' não encontrada no menu de mídia!")
            
        print(f"[FlowEditor] Realizando upload nativo de: {filename}...")
        with self.page.expect_file_chooser(timeout=8000) as fc_info:
            enviar_btn.click()
        file_chooser = fc_info.value
        file_chooser.set_files(image_path)
        
        # 3. Aguarda o upload e o processamento concluírem no Flow
        time.sleep(3)
        start_wait = time.time()
        while time.time() - start_wait < 30:
            uploading = self.page.evaluate("""() => {
                const text = document.body.innerText;
                return text.includes('Enviando') || text.includes('Carregando') || document.querySelector('[role="progressbar"]') !== null;
            }""")
            if not uploading:
                print(f"[FlowEditor] Upload concluído e processado com sucesso: {filename}")
                break
            time.sleep(1)
            
        time.sleep(1.5)
        self.page.keyboard.press("Escape")
        return filename

    def attach_reference(self, reference: str):
        """Anexa uma referência ao comando, aceitando tanto caminho local de arquivo quanto nome na biblioteca."""
        if os.path.exists(reference):
            ref_name = self.upload_reference_image(reference)
        else:
            ref_name = reference
            
        self.attach_reference_from_library(ref_name)

    def attach_reference_from_library(self, reference_name: str = "character_reference.jpg"):
        """Anexa um recurso de mídia existente da biblioteca do projeto como chip de referência."""
        self.page.keyboard.press("Escape")
        time.sleep(0.3)
        
        remove_chip_btn = self.page.locator("button[aria-label*='Remover'], button[aria-label*='remover'], button:has-text('close')").first
        if remove_chip_btn.is_visible():
            remove_chip_btn.click()
            time.sleep(0.4)
            
        add_btn = self.page.locator("button[aria-label='Adicionar elementos à caixa de comando']").first
        if not add_btn.is_visible():
            raise RuntimeError("Botão de adicionar elementos à caixa de comando não visível!")
        add_btn.click()
        time.sleep(1.2)
        
        search_input = self.page.locator("input[placeholder*='Pesquisar']").first
        if search_input.is_visible():
            search_input.fill(reference_name)
            time.sleep(0.8)
            
        char_item = self.page.locator(f"text='{reference_name}'").first
        if char_item.is_visible():
            char_item.click()
        else:
            self.page.mouse.click(400, 95)
        time.sleep(0.8)
        
        include_btn = self.page.locator("button:has-text('Incluir no comando')").first
        if include_btn.is_visible():
            include_btn.click()
        time.sleep(1.2)
        print(f"[FlowEditor] Chip de referência anexado com sucesso: {reference_name}")

    def submit_prompt(self, prompt: str, model: str = "Nano Banana 2", aspect_ratio: str = "16:9", reference: Optional[str] = None):
        """Insere o prompt diretamente no nó do ProseMirror e dispara a geração."""
        if reference:
            self.attach_reference(reference)
            
        self.verify_and_set_settings(model=model, aspect_ratio=aspect_ratio)
        
        pm = self.page.locator(".ProseMirror").first
        if not pm.is_visible():
            raise RuntimeError("Caixa de comando (.ProseMirror) não encontrada no canvas!")
            
        pm.click()
        time.sleep(0.3)
        
        # Injeção confiável com disparo de evento DOM input
        pm.evaluate("(el, text) => { el.innerText = text; el.dispatchEvent(new Event('input', { bubbles: true })); }", prompt)
        pm.click()
        flow_page_keyboard = self.page.keyboard
        flow_page_keyboard.press("End")
        flow_page_keyboard.type(" ")
        flow_page_keyboard.press("Backspace")
        time.sleep(0.5)
        
        submit_btn = self.page.locator("button[aria-label*='geração'], button[aria-label*='Iniciar'], button:has-text('arrow_forward')").first
        submit_btn.click()
        print("[FlowEditor] Prompt enviado com sucesso!")

    def wait_for_generation(self, timeout: int = 90) -> bool:
        """Aguarda reativamente o término da renderização."""
        start_time = time.time()
        time.sleep(4)
        while time.time() - start_time < timeout:
            state = self.page.evaluate("""() => {
                const text = document.body.innerText;
                const isGenerating = text.includes('%') || text.includes('Gerando') || text.includes('Criando') || document.querySelector('[role="progressbar"]') !== null;
                return { isGenerating: isGenerating };
            }""")
            if not state['isGenerating']:
                print("[FlowEditor] Renderização concluída com sucesso!")
                time.sleep(2)
                return True
            time.sleep(2)
            elapsed = int(time.time() - start_time)
            print(f"[FlowEditor] Gerando... ({elapsed}s)")
            
        print("[FlowEditor] Tempo limite esgotado para geração.")
        return False
