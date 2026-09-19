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
            needs_mode_change = "vídeo" in text.lower() or "video" in text.lower() or "720p" in text.lower()
            
            if not needs_model_change and not needs_ratio_change and not needs_mode_change:
                return
                
            # Abre popover
            self.page.keyboard.press("Escape")
            time.sleep(0.3)
            settings_btn.click()
            time.sleep(1)
            
            # 1. Garante que está na aba Imagem
            img_tab = self.page.locator("button:has-text('Imagem')").first
            if img_tab.is_visible():
                img_tab.click()
                time.sleep(0.5)
            
            # 2. Altera ratio se necessário
            ratio_btn = self.page.locator(f"button:has-text('{aspect_ratio}')").first
            if ratio_btn.is_visible():
                ratio_btn.click()
                time.sleep(0.5)
                print(f"[FlowEditor] Proporção alterada para {aspect_ratio}")
                    
            # 3. Altera modelo se necessário
            curr_model = self.page.locator("button[aria-label='Selecionar família de modelos']").first
            if curr_model.is_visible() and model not in curr_model.inner_text():
                curr_model.click()
                time.sleep(0.5)
                model_opt = self.page.locator(f"[role='option']:has-text('{model}'), button:has-text('{model}')").first
                if model_opt.is_visible():
                    model_opt.click()
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

    def set_video_settings(self, duration: int = 4, resolution: str = "720p", aspect_ratio: str = "16:9"):
        """Configura estritamente o modo de vídeo no Flow com Gemini Omni Flash 1.1 e validação de segundos."""
        if duration not in [4, 6, 8, 10]:
            raise ValueError(f"Duração inválida: {duration}s. O Google Flow suporta apenas 4s, 6s, 8s ou 10s.")
            
        settings_btn = self.page.locator("button[aria-label='Gatilho de configurações']").first
        if not settings_btn.is_visible():
            return
            
        text = settings_btn.inner_text()
        if "Vídeo" in text and f"{duration}s" in text and resolution in text and aspect_ratio in text:
            return
            
        self.page.keyboard.press("Escape")
        time.sleep(0.3)
        settings_btn.click()
        time.sleep(1)
        
        # 1. Aba Vídeo
        vid_tab = self.page.locator("button:has-text('Vídeo')").first
        if vid_tab.is_visible():
            vid_tab.click()
            time.sleep(0.5)
            
        # 2. Aspect Ratio (16:9 ou 9:16)
        ratio_btn = self.page.locator(f"button:has-text('{aspect_ratio}')").first
        if ratio_btn.is_visible():
            ratio_btn.click()
            time.sleep(0.3)
            
        # 3. Duração em segundos
        dur_btn = self.page.locator(f"button:has-text('{duration}s')").first
        if dur_btn.is_visible():
            dur_btn.click()
            time.sleep(0.3)
            
        # 4. Resolução (720p padrão)
        res_btn = self.page.locator(f"button:has-text('{resolution}')").first
        if res_btn.is_visible():
            res_btn.click()
            time.sleep(0.3)
            
        # 5. Garante modelo Omni 1.1 Flash (nunca Veo)
        model_btn = self.page.locator("button:has-text('Omni 1.1 Flash')").first
        if not model_btn.is_visible():
            curr_model_btn = self.page.locator("button[aria-label='Selecionar família de modelos']").first
            if curr_model_btn.is_visible():
                curr_model_btn.click()
                time.sleep(0.5)
                omni_opt = self.page.locator("[role='option']:has-text('Omni 1.1 Flash')").first
                if omni_opt.is_visible():
                    omni_opt.click()
                    time.sleep(0.3)
                    
        # 6. Quantidade x1
        x1_btn = self.page.locator("button:has-text('x1')").first
        if x1_btn.is_visible():
            x1_btn.click()
            time.sleep(0.3)
            
        self.page.keyboard.press("Escape")
        time.sleep(0.5)
        print(f"[FlowEditor] Configurações de vídeo ativadas: Omni 1.1 Flash | {duration}s | {resolution} | {aspect_ratio}")

    def submit_video_prompt(self, prompt: str, duration: Optional[int] = None, resolution: str = "720p", aspect_ratio: str = "16:9", reference: Optional[str] = None):
        """Dispara geração de vídeo (T2V ou I2V) exigindo obrigatoriamente a duração em segundos."""
        if duration is None:
            raise ValueError("A duração do vídeo em segundos (4, 6, 8, 10) é OBRIGATÓRIA! O pedido não pode ser aceito sem especificar os segundos.")
            
        if reference:
            self.attach_reference(reference)
            
        self.set_video_settings(duration=duration, resolution=resolution, aspect_ratio=aspect_ratio)
        
        pm = self.page.locator(".ProseMirror").first
        if not pm.is_visible():
            raise RuntimeError("Caixa de comando (.ProseMirror) não encontrada no canvas!")
            
        pm.click()
        time.sleep(0.2)
        pm.evaluate("(el, text) => { el.innerText = text; el.dispatchEvent(new Event('input', { bubbles: true })); }", prompt)
        pm.click()
        flow_page_keyboard = self.page.keyboard
        flow_page_keyboard.press("End")
        flow_page_keyboard.type(" ")
        flow_page_keyboard.press("Backspace")
        time.sleep(0.5)
        
        submit_btn = self.page.locator("button[aria-label*='geração'], button[aria-label*='Iniciar'], button:has-text('arrow_forward')").first
        submit_btn.click()
        print(f"[FlowEditor] Prompt de vídeo enviado com sucesso ({duration}s)!")

    def wait_for_video_generation(self, timeout: int = 180) -> bool:
        """Aguarda reativamente o término da renderização de vídeo."""
        print("[FlowEditor] Aguardando renderização do vídeo...")
        time.sleep(8)
        start_time = time.time()
        while time.time() - start_time < timeout:
            is_generating = self.page.evaluate("""() => {
                const text = document.body.innerText;
                return text.includes('%') || text.includes('Gerando') || text.includes('Criando') || document.querySelector('[role=\"progressbar\"]') !== null;
            }""")
            if not is_generating:
                elapsed = int(time.time() - start_time) + 8
                print(f"[FlowEditor] Renderização de vídeo concluída com sucesso em {elapsed}s!")
                time.sleep(2)
                return True
            time.sleep(3)
            elapsed = int(time.time() - start_time) + 8
            print(f"[FlowEditor] Renderizando vídeo... ({elapsed}s)")
            
        print("[FlowEditor] Tempo limite esgotado para renderização de vídeo.")
        return False

    def submit_batch_concurrent(self, prompts: list, model: str = "Nano Banana 2", aspect_ratio: str = "3:4", reference: Optional[str] = None, delay_between: float = 3.0) -> list:
        """Submete uma lista de prompts em lote de forma concorrente, aguardando apenas delay_between (default 3s) entre cada envio."""
        if not prompts:
            raise ValueError("Lista de prompts não pode ser vazia.")

        self.verify_and_set_settings(model=model, aspect_ratio=aspect_ratio)

        if reference:
            self.attach_reference(reference)
            time.sleep(1)

        pm = self.page.locator(".ProseMirror").first
        if not pm.is_visible():
            raise RuntimeError("Caixa de comando (.ProseMirror) não encontrada!")

        submit_btn = self.page.locator("button[aria-label*='geração'], button[aria-label*='Iniciar'], button:has-text('arrow_forward')").first

        submitted = []
        for i, p_info in enumerate(prompts):
            p_text = p_info if isinstance(p_info, str) else p_info.get("prompt", "")
            slide_id = i + 1 if isinstance(p_info, str) else p_info.get("slide", i + 1)

            print(f"[FlowEditor] Disparando Slide {slide_id}/{len(prompts)}...")
            pm.click()
            time.sleep(0.2)

            # Injeta texto preservando chip de mídia
            pm.evaluate("""(el, text) => {
                const textNodes = Array.from(el.childNodes).filter(node => node.nodeType === Node.TEXT_NODE);
                if (textNodes.length > 0) {
                    textNodes[0].textContent = text;
                } else {
                    el.appendChild(document.createTextNode(text));
                }
                el.dispatchEvent(new Event('input', { bubbles: true }));
            }""", p_text)

            # Toque de tecla para disparar reatividade do ProseMirror
            pm.click()
            self.page.keyboard.press("End")
            self.page.keyboard.type(" ")
            self.page.keyboard.press("Backspace")
            time.sleep(0.3)

            submit_btn.click()
            print(f"[FlowEditor] Slide {slide_id} enviado com sucesso! Aguardando {delay_between}s para o próximo...")
            submitted.append({"slide": slide_id, "prompt": p_text})

            # Intervalo inteligente: aguarda apenas delay_between (default 3s) para o próximo envio
            if i < len(prompts) - 1:
                time.sleep(delay_between)

        print(f"[FlowEditor] Todos os {len(submitted)} slides foram disparados com sucesso para renderização concorrente!")
        return submitted

    def wait_for_batch_completion(self, expected_count: int, timeout: int = 180) -> bool:
        """Aguarda todos os cards do lote atingirem 100% / finalizarem de forma concorrente."""
        print(f"[FlowEditor] Aguardando renderização concorrente de {expected_count} cards...")
        time.sleep(6)
        start_time = time.time()
        while time.time() - start_time < timeout:
            is_generating = self.page.evaluate("""() => {
                const text = document.body.innerText;
                return text.includes('%') || text.includes('Gerando') || text.includes('Criando') || document.querySelector('[role=\"progressbar\"]') !== null;
            }""")
            if not is_generating:
                elapsed = int(time.time() - start_time) + 6
                print(f"[FlowEditor] Renderização de todos os {expected_count} cards concluída com sucesso em {elapsed}s!")
                time.sleep(2)
                return True
            time.sleep(2.5)
            elapsed = int(time.time() - start_time) + 6
            print(f"[FlowEditor] Renderizando lote concorrente... ({elapsed}s)")

        print("[FlowEditor] Tempo limite esgotado para renderização do lote.")
        return False

