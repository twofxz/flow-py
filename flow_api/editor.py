from .logger import log
import os
import time
from typing import Optional, List, Union, Dict
from playwright.sync_api import Page

# Política Estrita de Modelos da Skill:
# Permitidos: 'Nano Banana 2', 'Nano Banana Pro', 'Veo 2'
# Proibidos: 'Nano Banana 2 Lite' (baixa fidelidade)
ALLOWED_IMAGE_MODELS = ["Nano Banana 2", "Nano Banana Pro"]

class FlowEditor:
    def __init__(self, page: Page):
        self.page = page
        self.uploaded_files = set()

    def verify_and_set_settings(self, model: str = "Nano Banana 2", aspect_ratio: str = "16:9"):
        """Garante que o modelo e o aspect ratio configurados sigam a política estrita."""
        if "lite" in model.lower():
            raise ValueError(f"Modelo proibido: {model}. A skill requer Nano Banana 2 ou Nano Banana Pro.")
            
        settings_btn = self.page.locator("button[aria-label='Gatilho de configurações']").first
        if settings_btn.is_visible():
            text = settings_btn.inner_text()
            safe_text = text.encode('ascii', errors='replace').decode('ascii')
            log(f"[FlowEditor] Configurações ativas no canvas: {repr(safe_text)}")
            
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
                log(f"[FlowEditor] Proporção alterada para {aspect_ratio}")
                    
            # 3. Altera modelo se necessário
            curr_model = self.page.locator("button[aria-label='Selecionar família de modelos']").first
            if curr_model.is_visible() and model not in curr_model.inner_text():
                curr_model.click()
                time.sleep(0.5)
                model_opt = self.page.locator(f"[role='option']:has-text('{model}'), button:has-text('{model}')").first
                if model_opt.is_visible():
                    model_opt.click()
                    time.sleep(0.5)
                    log(f"[FlowEditor] Modelo alterado para {model}")
                    
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
            
        log(f"[FlowEditor] Realizando upload nativo de: {filename}...")
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
                log(f"[FlowEditor] Upload concluído e processado com sucesso: {filename}")
                break
            time.sleep(1)
            
        time.sleep(1.5)
        self.page.keyboard.press("Escape")
        return filename

    def attach_references(self, references: List[str]):
        """Anexa múltiplas referências visuais à caixa de comando, garantindo upload nativo se necessário."""
        if not references:
            return
            
        ref_paths = references if isinstance(references, list) else [references]
                
        # 1. Limpa chips pré-existentes na barra de comando
        chips = self.page.locator("button.chip-container, button[aria-label='Elemento']").all()
        for ch in chips:
            try:
                ch.locator("button, [role='button'], .close, [aria-label*='remover']").first.click(force=True)
            except Exception:
                try:
                    ch.click(force=True)
                except Exception:
                    pass
        time.sleep(0.3)
        self.page.keyboard.press("Escape")
        time.sleep(0.2)

        # 2. Anexa cada uma das referências
        add_btn = self.page.locator("button[aria-label*='Adicionar elementos']").first
        if not add_btn.is_visible():
            raise RuntimeError("Botão de adicionar elementos à caixa de comando não visível!")

        for ref in ref_paths:
            base_name = os.path.splitext(os.path.basename(ref))[0]
            is_file = os.path.exists(ref)

            # Abre o popover 'Adicionar elementos'
            add_btn.click(force=True)
            time.sleep(0.8)

            overlay = self.page.locator(".cdk-overlay-pane").first
            if not overlay.is_visible():
                raise RuntimeError("Overlay de seleção de elementos não abriu!")

            # Procura item existente na lista
            target = overlay.locator(f".asset-item:has-text('{base_name}')").first
            if not target.is_visible() and is_file:
                # Faz upload diretamente via botão Enviar mídia do próprio overlay
                upload_btn = overlay.locator("button:has-text('Enviar mídia'), button:has-text('Enviar')").first
                if upload_btn.is_visible():
                    log(f"[FlowEditor] Enviando arquivo de referência: {os.path.basename(ref)}...")
                    with self.page.expect_file_chooser(timeout=8000) as fc_info:
                        upload_btn.click()
                    fc_info.value.set_files(os.path.abspath(ref))
                    
                    # Aguarda término do upload (status 'Enviando' sumir)
                    start_wait = time.time()
                    while time.time() - start_wait < 30:
                        target = overlay.locator(f".asset-item:has-text('{base_name}')").first
                        if target.is_visible():
                            text = target.inner_text()
                            if "Enviando" not in text and "Carregando" not in text:
                                break
                        time.sleep(1)

            if not target.is_visible():
                target = overlay.locator(f".asset-item:has-text('{os.path.basename(ref)}')").first
            if not target.is_visible():
                target = overlay.locator(".asset-item").first

            if target.is_visible():
                classes = target.get_attribute("class") or ""
                if "asset-item-active" not in classes:
                    target.click(force=True)
                    time.sleep(0.5)

                include_btn = overlay.locator("button:has-text('Incluir no comando'), .detail-add-to-prompt").first
                if include_btn.is_visible() and not include_btn.is_disabled():
                    include_btn.click(force=True)
                    time.sleep(0.5)

            self.page.keyboard.press("Escape")
            time.sleep(0.3)

        # Validação estrita: chips PRECISAM estar presentes na barra de comando
        active_chips = self.page.locator("button.chip-container, button[aria-label='Elemento']").all()
        if len(active_chips) == 0:
            raise RuntimeError(f"FALHA CRÍTICA: Chip de referência não foi anexado à barra de comando para '{references}'! Abortando geração para evitar perda de consistência.")
        log(f"[FlowEditor] {len(active_chips)} chip(s) de referência anexado(s) e validados com sucesso!")

    def attach_reference(self, reference: str):
        """Anexa uma única referência visual (retrocompatibilidade)."""
        self.attach_references([reference])

    def attach_reference_from_library(self, reference_name: str = "character_reference.jpg"):
        """Anexa um recurso de mídia existente da biblioteca do projeto como chip de referência."""
        self.attach_references([reference_name])

    def submit_prompt(self, prompt: str, model: str = "Nano Banana 2", aspect_ratio: str = "16:9", reference: Optional[Union[str, List[str]]] = None):
        """Insere o prompt diretamente no nó do ProseMirror e dispara a geração."""
        if reference:
            if isinstance(reference, list):
                self.attach_references(reference)
            else:
                self.attach_references([reference])
            
        self.verify_and_set_settings(model=model, aspect_ratio=aspect_ratio)
        
        pm = self.page.locator(".ProseMirror").first
        if not pm.is_visible():
            raise RuntimeError("Caixa de comando (.ProseMirror) não encontrada no canvas!")
            
        pm.click()
        time.sleep(0.2)
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Backspace")
        time.sleep(0.1)

        self.page.keyboard.type(prompt)
        time.sleep(0.3)
        
        # Validação estrita se referência foi solicitada
        if reference:
            active_chips = self.page.locator("button.chip-container, button[aria-label='Elemento']").all()
            if len(active_chips) == 0:
                raise RuntimeError("FALHA CRÍTICA: O chip de referência desapareceu antes do disparo da geração!")
        
        submit_btn = self.page.locator("button[aria-label*='geração'], button[aria-label*='Iniciar'], button.generate-icon-button, button:has-text('arrow_forward')").first
        submit_btn.click()
        log("[FlowEditor] Prompt enviado com sucesso!")

    def check_error_alerts(self) -> Optional[str]:
        """Verifica se há alertas de erro, bloqueio de segurança ou limite de cota no DOM."""
        return self.page.evaluate("""() => {
            const alerts = Array.from(document.querySelectorAll('.mat-mdc-snack-bar-container, [role="alert"], [role="status"]'));
            for (const a of alerts) {
                const text = a.innerText || '';
                const lower = text.toLowerCase();
                if (lower.includes('não foi possível') || lower.includes('erro') || lower.includes('diretriz') || lower.includes('política') || lower.includes('policy') || lower.includes('limite') || lower.includes('quota') || lower.includes('blocked')) {
                    return text.trim();
                }
            }
            return null;
        }""")

    def wait_for_generation(self, timeout: int = 90) -> bool:
        """Aguarda reativamente o término da renderização com monitoramento ativo de erros e políticas."""
        start_time = time.time()
        time.sleep(4)
        while time.time() - start_time < timeout:
            err = self.check_error_alerts()
            if err:
                log(f"[FlowEditor] ❌ Erro detectado no Google Flow: {err}")
                raise RuntimeError(f"Google Flow Error: {err}")

            state = self.page.evaluate("""() => {
                const text = document.body.innerText;
                const isGenerating = text.includes('%') || text.includes('Gerando') || text.includes('Criando') || document.querySelector('[role="progressbar"]') !== null;
                return { isGenerating: isGenerating };
            }""")
            if not state['isGenerating']:
                log("[FlowEditor] Renderização concluída com sucesso!")
                time.sleep(2)
                return True
            time.sleep(2)
            elapsed = int(time.time() - start_time)
            log(f"[FlowEditor] Gerando... ({elapsed}s)")
            
        log("[FlowEditor] Tempo limite esgotado para geração.")
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
        log(f"[FlowEditor] Configurações de vídeo ativadas: Omni 1.1 Flash | {duration}s | {resolution} | {aspect_ratio}")

    def submit_video_prompt(self, prompt: str, duration: Optional[int] = None, resolution: str = "720p", aspect_ratio: str = "16:9", reference: Optional[Union[str, List[str]]] = None):
        """Dispara geração de vídeo (T2V ou I2V) exigindo obrigatoriamente a duração em segundos (4s, 6s, 8s, 10s)."""
        if duration is None:
            raise ValueError("A duração do vídeo em segundos (4, 6, 8, 10) é OBRIGATÓRIA! O pedido não pode ser aceito sem especificar os segundos.")

        # 1. Configura parâmetros de vídeo (Omni 1.1 Flash, duração, resolução e aspect ratio)
        self.set_video_settings(duration=duration, resolution=resolution, aspect_ratio=aspect_ratio)

        # 2. Anexa referências de imagem (Image-to-Video)
        if reference:
            refs = reference if isinstance(reference, list) else [reference]
            self.attach_references(refs)

        pm = self.page.locator(".ProseMirror").first
        if not pm.is_visible():
            raise RuntimeError("Caixa de comando (.ProseMirror) não encontrada no canvas!")

        # 3. Insere prompt preservando chips anexados
        pm.click(force=True)
        time.sleep(0.2)
        pm.evaluate("""(el, text) => {
            let p = el.querySelector('p');
            if (!p) {
                p = document.createElement('p');
                el.appendChild(p);
            }
            p.innerText = text;
            el.dispatchEvent(new Event('input', { bubbles: true }));
        }""", prompt)

        self.page.keyboard.press("End")
        self.page.keyboard.type(" ")
        self.page.keyboard.press("Backspace")
        time.sleep(0.5)

        submit_btn = self.page.locator("button[aria-label*='geração'], button[aria-label*='Iniciar'], button:has-text('arrow_forward')").first
        submit_btn.click(force=True)
        log(f"[FlowEditor] Prompt de vídeo enviado com sucesso ({duration}s - Omni 1.1 Flash)!")

    def wait_for_video_generation(self, timeout: int = 180) -> bool:
        """Aguarda reativamente o término da renderização de vídeo com monitoramento ativo de erros e políticas."""
        log("[FlowEditor] Aguardando início da renderização do vídeo...")
        start_time = time.time()

        # 1. Aguarda início efetivo da renderização (até 15s)
        time.sleep(3)
        for _ in range(12):
            err = self.check_error_alerts()
            if err:
                raise RuntimeError(f"Google Flow Error: {err}")

            status = self.page.evaluate("""() => {
                const text = document.body.innerText;
                const hasProgress = text.includes('%') || text.includes('Gerando') || text.includes('Criando') || document.querySelector('[role=\"progressbar\"]') !== null;
                const tiles = document.querySelectorAll('flow-grid-tile-container');
                const firstTileGenerating = tiles.length > 0 && !tiles[0].innerText.includes('play_circle') && (tiles[0].querySelector('[role=\"progressbar\"]') !== null || tiles[0].innerText.includes('%'));
                return hasProgress || firstTileGenerating;
            }""")
            if status:
                break
            time.sleep(1)

        log("[FlowEditor] Renderização em andamento. Monitorando conclusão...")
        # 2. Loop de monitoramento até conclusão efetiva
        while time.time() - start_time < timeout:
            err = self.check_error_alerts()
            if err:
                log(f"[FlowEditor] ❌ Erro detectado no Google Flow: {err}")
                raise RuntimeError(f"Google Flow Error: {err}")

            state = self.page.evaluate("""() => {
                const text = document.body.innerText;
                const isGenerating = text.includes('%') || text.includes('Gerando') || text.includes('Criando') || document.querySelector('[role=\"progressbar\"]') !== null;
                const tiles = document.querySelectorAll('flow-grid-tile-container');
                const firstTileReady = tiles.length > 0 && tiles[0].innerText.includes('play_circle');
                return { isGenerating: isGenerating, firstTileReady: firstTileReady };
            }""")

            if not state['isGenerating'] and state['firstTileReady']:
                elapsed = int(time.time() - start_time)
                log(f"[FlowEditor] Renderização de vídeo concluída com sucesso em {elapsed}s!")
                log("[FlowEditor] Aguardando estabilização do arquivo MP4 no CDN do Google (15s)...")
                time.sleep(15)
                return True

            time.sleep(3)
            elapsed = int(time.time() - start_time)
            log(f"[FlowEditor] Renderizando vídeo... ({elapsed}s)")

        log("[FlowEditor] Tempo limite esgotado para renderização de vídeo.")
        return False

    def submit_batch_concurrent(
        self,
        prompts: list,
        model: str = "Nano Banana 2",
        aspect_ratio: str = "3:4",
        reference: Optional[Union[str, List[str]]] = None,
        delay_between: float = 3.0
    ) -> list:
        """Submete uma lista de prompts em lote de forma concorrente, garantindo re-anexação rápida de referências a cada slide."""
        if not prompts:
            raise ValueError("Lista de prompts não pode ser vazia.")

        self.verify_and_set_settings(model=model, aspect_ratio=aspect_ratio)

        # Prepara referências base
        base_refs = []
        if reference:
            base_refs = reference if isinstance(reference, list) else [reference]
            for r in base_refs:
                if os.path.exists(r):
                    self.upload_reference_image(r)

        pm = self.page.locator(".ProseMirror").first
        if not pm.is_visible():
            raise RuntimeError("Caixa de comando (.ProseMirror) não encontrada!")

        submit_btn = self.page.locator("button[aria-label*='geração'], button[aria-label*='Iniciar'], button:has-text('arrow_forward')").first

        submitted = []
        for i, p_info in enumerate(prompts):
            p_text = p_info if isinstance(p_info, str) else p_info.get("prompt", "")
            slide_id = i + 1 if isinstance(p_info, str) else p_info.get("slide", i + 1)

            # Suporte a referências específicas por slide no manifesto
            slide_refs = None
            if isinstance(p_info, dict):
                slide_refs = p_info.get("references") or ([p_info.get("reference")] if p_info.get("reference") else None)
            if not slide_refs:
                slide_refs = base_refs

            log(f"[FlowEditor] Disparando Slide {slide_id}/{len(prompts)}...")

            # 1. Garante que os chips de referência estejam anexados (Flow limpa a cada envio)
            if slide_refs:
                self.attach_references(slide_refs)

            # 2. Aguarda o botão de envio estar pronto/habilitado
            start_wait = time.time()
            while time.time() - start_wait < 15:
                is_ready = self.page.evaluate("""() => {
                    const btn = document.querySelector("button[aria-label*='geração'], button[aria-label*='Iniciar'], button.generate-icon-button");
                    return btn && !btn.disabled && btn.getAttribute('aria-disabled') !== 'true';
                }""")
                if is_ready:
                    break
                time.sleep(0.5)

            # 3. Insere o prompt na caixa ProseMirror
            pm.click(force=True)
            time.sleep(0.2)
            self.page.keyboard.press("Control+A")
            self.page.keyboard.press("Backspace")
            time.sleep(0.1)

            self.page.keyboard.type(p_text)
            time.sleep(0.3)

            # Validação estrita de persistência do chip antes de enviar
            if slide_refs:
                active_chips = self.page.locator("button.chip-container, button[aria-label='Elemento']").all()
                if len(active_chips) == 0:
                    raise RuntimeError(f"FALHA CRÍTICA: Chip de referência desapareceu antes do envio do Slide {slide_id}!")

            # 4. Clica no botão de iniciar geração
            submit_btn.click(force=True)
            log(f"[FlowEditor] Slide {slide_id} enviado com sucesso! Aguardando {delay_between}s para o próximo...")
            submitted.append({"slide": slide_id, "prompt": p_text})

            # Intervalo entre envios (padrão 3s)
            if i < len(prompts) - 1:
                time.sleep(delay_between)

        log(f"[FlowEditor] Todos os {len(submitted)} slides foram disparados com sucesso para renderização concorrente!")
        return submitted

    def wait_for_batch_completion(self, expected_count: int, timeout: int = 180) -> bool:
        """Aguarda todos os cards do lote atingirem 100% / finalizarem de forma concorrente."""
        log(f"[FlowEditor] Aguardando renderização concorrente de {expected_count} cards...")
        time.sleep(6)
        start_time = time.time()
        while time.time() - start_time < timeout:
            is_generating = self.page.evaluate("""() => {
                const text = document.body.innerText;
                return text.includes('%') || text.includes('Gerando') || text.includes('Criando') || document.querySelector('[role=\"progressbar\"]') !== null;
            }""")
            if not is_generating:
                elapsed = int(time.time() - start_time) + 6
                log(f"[FlowEditor] Renderização de todos os {expected_count} cards concluída com sucesso em {elapsed}s!")
                time.sleep(2)
                return True
            time.sleep(2.5)
            elapsed = int(time.time() - start_time) + 6
            log(f"[FlowEditor] Renderizando lote concorrente... ({elapsed}s)")

        log("[FlowEditor] Tempo limite esgotado para renderização do lote.")
        return False

