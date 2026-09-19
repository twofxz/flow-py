"""
Google Flow MCP Server
Servidor MCP nativo baseado no SDK oficial da Anthropic / Model Context Protocol.
Compatível com Claude Desktop, Claude Code, Cursor, OpenCode e Windsurf.
"""

import os
import sys
import json
from typing import Optional, List

try:
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        FastMCP = None

from .client import FlowClient
from .editor import FlowEditor
from .downloader import FlowDownloader

def create_mcp_server():
    if FastMCP is None:
        raise RuntimeError("O pacote 'mcp' não está instalado. Instale com: pip install mcp")

    mcp = FastMCP("google-flow")

    @mcp.tool()
    def generate_image(
        prompt: str,
        ratio: str = "16:9",
        model: str = "Nano Banana 2",
        reference_image: Optional[str] = None,
        resolution: str = "1K"
    ) -> str:
        """Gera uma imagem cinematográfica de alta qualidade no Google Flow e salva localmente em resolução nativa original (1K/2K).

        Args:
            prompt: Descrição visual detalhada da cena.
            ratio: Proporção da imagem ('16:9', '9:16', '1:1', '3:4', '4:3').
            model: Modelo ('Nano Banana 2' ou 'Nano Banana Pro').
            reference_image: Caminho local de imagem de referência para consistência de personagem/estilo.
            resolution: Resolução nativa ('1K' ou '2K').
        """
        client = FlowClient(session="mcp_agent")
        client.start_browser_if_needed()
        client.connect()
        client.ensure_canvas()

        editor = FlowEditor(client.page)
        downloader = FlowDownloader(client.page, client.download_dir)

        ref = [reference_image] if reference_image else None
        editor.submit_prompt(prompt, model=model, aspect_ratio=ratio, reference=ref)
        
        success = editor.wait_for_generation(timeout=90)
        if not success:
            return json.dumps({"success": False, "error": "Timeout na geração da imagem."})

        downloader.open_viewer(force_newest=True)
        saved_file = downloader.download_current(resolution=resolution)

        return json.dumps({
            "success": True,
            "type": "image",
            "model": model,
            "ratio": ratio,
            "resolution": resolution,
            "reference": reference_image,
            "downloaded_file": saved_file,
            "output_dir": client.download_dir
        }, indent=2)

    @mcp.tool()
    def generate_video(
        prompt: str,
        duration: int = 4,
        ratio: str = "16:9",
        reference_image: Optional[str] = None
    ) -> str:
        """Gera um vídeo nativo MP4 no Google Flow usando Gemini Omni Flash 1.1 (Text-to-Video ou Image-to-Video).

        Args:
            prompt: Direção de cena e movimento de câmera do vídeo.
            duration: Duração OBRIGATÓRIA em segundos. O Google Flow aceita exclusivamente: 4, 6, 8 ou 10.
            ratio: Proporção do vídeo ('16:9' widescreen ou '9:16' vertical Reels/Stories).
            reference_image: Caminho local de imagem base para geração Image-to-Video (I2V).
        """
        if duration not in [4, 6, 8, 10]:
            return json.dumps({
                "success": False,
                "error": f"Duração inválida ({duration}s). O Google Flow suporta nativamente apenas 4, 6, 8 ou 10 segundos."
            })

        client = FlowClient(session="mcp_agent")
        client.start_browser_if_needed()
        client.connect()
        client.ensure_canvas()

        editor = FlowEditor(client.page)
        downloader = FlowDownloader(client.page, client.download_dir)

        ref = [reference_image] if reference_image else None
        editor.submit_video_prompt(prompt, duration=duration, resolution="720p", aspect_ratio=ratio, reference=ref)

        success = editor.wait_for_video_generation(timeout=180)
        if not success:
            return json.dumps({"success": False, "error": "Timeout na renderização do vídeo."})

        saved_file = downloader.download_video(resolution="720p")

        return json.dumps({
            "success": True,
            "type": "video",
            "model": "Omni 1.1 Flash",
            "duration": f"{duration}s",
            "ratio": ratio,
            "resolution": "720p",
            "reference": reference_image,
            "downloaded_file": saved_file,
            "output_dir": client.download_dir
        }, indent=2)

    @mcp.tool()
    def flow_status() -> str:
        """Verifica o status da conexão com o Google Flow, autenticação da conta e projeto ativo."""
        client = FlowClient(session="mcp_agent")
        status = client.check_auth_status()
        return json.dumps(status, indent=2)

    return mcp

def main():
    server = create_mcp_server()
    server.run()

if __name__ == "__main__":
    main()
