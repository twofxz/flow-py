"""
CLI do Motor Google Flow
Interface unificada para execução rápida via terminal e integração nativa com Antigravity.
"""

import os
import sys
import argparse
import json
from .client import FlowClient
from .editor import FlowEditor
from .downloader import FlowDownloader
from .logger import log

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Google Flow Automation Engine CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Comando: generate
    gen_parser = subparsers.add_parser("generate", help="Gera imagens no Google Flow e realiza download nativo")
    gen_parser.add_argument("--prompt", type=str, required=True, help="Prompt textual da imagem")
    gen_parser.add_argument("--reference", type=str, default=None, help="Nome do arquivo na biblioteca ou caminho da imagem local")
    gen_parser.add_argument("--reference-image", type=str, default=None, help="Alias para caminho da imagem de referência local")
    gen_parser.add_argument("--references", nargs="+", default=None, help="Múltiplas imagens de referência (locais ou na biblioteca)")
    gen_parser.add_argument("--filename", type=str, default=None, help="Nome personalizado do arquivo salvo (ex: meu_personagem.jpeg)")
    gen_parser.add_argument("--model", type=str, default="Nano Banana 2", help="Modelo de geração")
    gen_parser.add_argument("--ratio", type=str, default="16:9", help="Proporção da imagem (16:9, 9:16, 1:1, 3:4)")
    gen_parser.add_argument("--session", type=str, default=None, help="Identificador da sessão/agente (ex: antigravity, codex)")
    gen_parser.add_argument("--output-dir", type=str, default=None, help="Pasta de destino dos arquivos")
    gen_parser.add_argument("--resolution", type=str, default="1K", choices=["1K", "2K"], help="Resolução nativa de download")
    gen_parser.add_argument("--timeout", type=int, default=90, help="Tempo limite de geração em segundos")
    gen_parser.add_argument("--json", action="store_true", help="Retorna saída formatada em JSON")
    gen_parser.add_argument("--head", action="store_true", help="Executa com navegador visível para depuração")

    # Comando: video
    vid_parser = subparsers.add_parser("video", help="Gera vídeos no Google Flow usando Gemini Omni Flash 1.1")
    vid_parser.add_argument("--prompt", type=str, required=True, help="Prompt textual do vídeo")
    vid_parser.add_argument("--duration", type=int, required=True, choices=[4, 6, 8, 10], help="Duração OBRIGATÓRIA do vídeo em segundos (4, 6, 8 ou 10)")
    vid_parser.add_argument("--reference", type=str, default=None, help="Nome do arquivo na biblioteca ou caminho da imagem local para I2V")
    vid_parser.add_argument("--reference-image", type=str, default=None, help="Alias para caminho da imagem de referência local")
    vid_parser.add_argument("--references", nargs="+", default=None, help="Múltiplas imagens de referência para I2V")
    vid_parser.add_argument("--filename", type=str, default=None, help="Nome personalizado do vídeo salvo (ex: meu_video.mp4)")
    vid_parser.add_argument("--ratio", type=str, default="16:9", choices=["16:9", "9:16"], help="Proporção do vídeo (16:9 ou 9:16)")
    vid_parser.add_argument("--resolution", type=str, default="720p", choices=["720p"], help="Resolução do vídeo (estritamente 720p)")
    vid_parser.add_argument("--session", type=str, default=None, help="Identificador da sessão/agente (ex: antigravity, codex)")
    vid_parser.add_argument("--output-dir", type=str, default=None, help="Pasta de destino dos arquivos")
    vid_parser.add_argument("--timeout", type=int, default=180, help="Tempo limite de geração em segundos")
    vid_parser.add_argument("--json", action="store_true", help="Retorna saída formatada em JSON")
    vid_parser.add_argument("--head", action="store_true", help="Executa com navegador visível para depuração")

    # Comando: batch (geração concorrente rápida - 3s delay)
    batch_parser = subparsers.add_parser("batch", help="Gera múltiplos slides concorrentemente (delay inteligente de 3s por prompt)")
    batch_parser.add_argument("--manifest", type=str, required=True, help="Caminho do arquivo JSON com os prompts")
    batch_parser.add_argument("--reference", type=str, default=None, help="Nome do arquivo de referência na biblioteca ou caminho local")
    batch_parser.add_argument("--reference-image", type=str, default=None, help="Alias para caminho local da referência")
    batch_parser.add_argument("--references", nargs="+", default=None, help="Múltiplas imagens de referência para o lote")
    batch_parser.add_argument("--model", type=str, default="Nano Banana 2", choices=["Nano Banana 2", "Nano Banana Pro"], help="Modelo de imagem")
    batch_parser.add_argument("--ratio", type=str, default="3:4", help="Proporção da imagem (3:4, 16:9, 9:16, 1:1)")
    batch_parser.add_argument("--delay", type=float, default=3.0, help="Intervalo em segundos entre envios (padrão: 3.0s)")
    batch_parser.add_argument("--session", type=str, default=None, help="Identificador da sessão/agente (ex: antigravity, codex)")
    batch_parser.add_argument("--output-dir", type=str, default=None, help="Pasta de destino dos arquivos")
    batch_parser.add_argument("--resolution", type=str, default="1K", choices=["1K", "2K"], help="Resolução de download")
    batch_parser.add_argument("--timeout", type=int, default=180, help="Tempo limite total de renderização do lote")
    batch_parser.add_argument("--json", action="store_true", help="Retorna saída formatada em JSON")
    batch_parser.add_argument("--head", action="store_true", help="Executa com navegador visível para depuração")

    # Comando: login (onboarding)
    login_parser = subparsers.add_parser("login", help="Inicia o navegador dedicado para login interativo com a conta Google")
    login_parser.add_argument("--session", type=str, default=None, help="Identificador da sessão/agente")

    # Comando: status / doctor
    status_parser = subparsers.add_parser("status", help="Diagnostica a conexão, perfil, autenticação e projeto ativo do Google Flow")
    status_parser.add_argument("--session", type=str, default=None, help="Identificador da sessão/agente")
    status_parser.add_argument("--head", action="store_true", help="Executa com navegador visível para depuração")

    # Comando: auth-check (padrão notebooklm rápido)
    auth_parser = subparsers.add_parser("auth-check", help="Verifica rapidamente a autenticação e estado da sessão (padrão notebooklm)")
    auth_parser.add_argument("--json", action="store_true", help="Retorna o resultado formatado em JSON")
    auth_parser.add_argument("--session", type=str, default=None, help="Identificador da sessão/agente")

    # Comando: serve (OpenAI-compatible FastAPI)
    serve_parser = subparsers.add_parser("serve", help="Inicia a API local compatível com OpenAI (POST /v1/images/generations)")
    serve_parser.add_argument("--host", type=str, default="127.0.0.1", help="Host do servidor (padrão: 127.0.0.1)")
    serve_parser.add_argument("--port", type=int, default=8000, help="Porta do servidor (padrão: 8000)")

    # Comando: mcp (Model Context Protocol para Claude/Cursor/OpenCode)
    mcp_parser = subparsers.add_parser("mcp", help="Inicia o servidor MCP nativo via stdio para Claude Desktop, Cursor e OpenCode")

    # Comando: test-connection
    test_parser = subparsers.add_parser("test-connection", help="Testa e valida conexão com a aba ativa do Google Flow")
    test_parser.add_argument("--session", type=str, default=None, help="Identificador da sessão/agente (ex: antigravity, codex)")
    test_parser.add_argument("--head", action="store_true", help="Executa com navegador visível para depuração")

    # Comando: download-all
    dl_parser = subparsers.add_parser("download-all", help="Baixa todas as imagens da galeria ativa")
    dl_parser.add_argument("--session", type=str, default=None, help="Identificador da sessão/agente (ex: antigravity, codex)")
    dl_parser.add_argument("--output-dir", type=str, default=None, help="Pasta de destino dos arquivos")
    dl_parser.add_argument("--resolution", type=str, default="1K", choices=["1K", "2K"], help="Resolução de download")
    dl_parser.add_argument("--count", type=int, default=None, help="Número máximo de itens para baixar")
    dl_parser.add_argument("--json", action="store_true", help="Retorna o resultado formatado em JSON")
    dl_parser.add_argument("--head", action="store_true", help="Executa com navegador visível para depuração")

    # Comando: stop / down (daemon shutdown)
    stop_parser = subparsers.add_parser("stop", help="Encerra com segurança instâncias em segundo plano do Chromium na porta 9222")
    down_parser = subparsers.add_parser("down", help="Alias para 'stop'")

    return parser

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    parser = build_parser()
    args = parser.parse_args()

    # Roteamento especial para comandos que gerenciam seus próprios ciclos
    if args.command in ["stop", "down"]:
        client = FlowClient()
        stopped = client.stop_background_process()
        if stopped:
            print("🛑 Processo em segundo plano do Google Flow encerrado com sucesso.")
        else:
            print("ℹ️ Nenhum processo ativo do Google Flow encontrado para encerrar.")
        return

    if args.command == "serve":
        import uvicorn
        from .server import app
        print(f"[FlowAPI] Iniciando servidor OpenAI-compatível em http://{args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
        return

    if args.command == "mcp":
        from .mcp_server import main as mcp_main
        mcp_main()
        return

    if args.command == "auth-check":
        client = FlowClient(session=getattr(args, "session", None), headless=True)
        try:
            client.start_browser_if_needed()
            auth = client.check_auth_status()
            if getattr(args, "json", False):
                print(json.dumps(auth, indent=2))
            else:
                if auth.get("authenticated"):
                    print("✅ Autenticado: Sim")
                    print(f"🔗 Projeto: {auth.get('url')}")
                    print(f"📁 Perfil: {auth.get('profile_dir')}")
                else:
                    print("❌ Não autenticado. Execute 'google-flow login' para iniciar a sessão.")
                    if auth.get("error"):
                        print(f"Detalhes: {auth.get('error')}")
            if not auth.get("authenticated"):
                sys.exit(1)
        finally:
            client.close()
        return

    is_login = args.command == "login"
    headless = False if is_login else not getattr(args, "head", False)
    client = FlowClient(
        download_dir=getattr(args, "output_dir", None),
        session=getattr(args, "session", None),
        headless=headless
    )

    try:
        if args.command == "login":
            print("=" * 60)
            print("🔐 GOOGLE FLOW - LOGIN & ONBOARDING")
            print("=" * 60)
            client.start_browser_if_needed()
            page = client.connect()

            # Restaura a janela se estiver minimizada e traz para a frente via CDP
            try:
                cdp = client.context.new_cdp_session(page)
                win = cdp.send("Browser.getWindowForTarget")
                cdp.send("Browser.setWindowBounds", {
                    "windowId": win["windowId"],
                    "bounds": {"windowState": "normal"}
                })
                page.bring_to_front()
            except Exception:
                pass

            client.dismiss_modals()
            auth = client.check_auth_status()

            if auth.get("authenticated"):
                print("\n✅ Você já está autenticado com sucesso no Google Flow!")
                print(f"🔗 Projeto ativo: {auth.get('url')}")
                print(f"📁 Perfil salvo em: {auth.get('profile_dir')}")
                print("\nVocê não precisa fazer login novamente. O sistema está 100% pronto para gerar imagens e vídeos!")
                client.stop_background_process()
                return

            print("\n👉 O navegador foi aberto na página do Google Flow.")
            print("👉 Verifique a janela do Google Chrome aberta na sua barra de tarefas.")
            print("👉 Faça login com sua conta Google e aceite os termos de serviço caso seja o primeiro acesso.")
            print("\nQuando estiver logado e visualizando o painel do Flow, pressione [ENTER] aqui no terminal...")
            try:
                input()
            except EOFError:
                pass
            
            client.dismiss_modals()
            auth = client.check_auth_status()
            if auth.get("authenticated"):
                print("\n✅ Autenticação confirmada com sucesso!")
                print(f"🔗 Projeto ativo: {auth.get('url')}")
                print(f"📁 Perfil salvo em: {auth.get('profile_dir')}")
                print("\nPronto para gerar imagens e vídeos via CLI, MCP ou Python API!")
                client.stop_background_process()
            else:
                print("\n⚠️ Não foi possível confirmar o login:")
                print(json.dumps(auth, indent=2))
                client.stop_background_process()
            return

        elif args.command == "status":
            client.start_browser_if_needed()
            auth = client.check_auth_status()
            print(json.dumps(auth, indent=2))
            return

        page = client.connect()
        editor = FlowEditor(page)
        downloader = FlowDownloader(page, client.download_dir)

        if args.command == "test-connection":
            client.ensure_canvas()
            print(json.dumps({
                "success": True,
                "status": "connected",
                "session": client.session,
                "flow_url": page.url,
                "title": page.title()
            }, indent=2))
            return

        elif args.command == "generate":
            client.ensure_canvas()
            ref = args.references or args.reference or args.reference_image
            editor.submit_prompt(args.prompt, model=args.model, aspect_ratio=args.ratio, reference=ref)
            success = editor.wait_for_generation(timeout=args.timeout)
            if not success:
                print(json.dumps({"success": False, "error": "Timeout na renderização"}))
                sys.exit(1)

            downloader.open_viewer()
            saved_file = downloader.download_current(resolution=args.resolution, filename=args.filename)
            abs_saved_file = os.path.abspath(saved_file) if saved_file else None
            abs_output_dir = os.path.abspath(client.download_dir) if client.download_dir else None
            print(json.dumps({
                "success": True,
                "session": client.session,
                "model": args.model,
                "ratio": args.ratio,
                "reference": ref,
                "downloaded_file": abs_saved_file,
                "output_dir": abs_output_dir
            }, indent=2))

        elif args.command == "video":
            client.ensure_canvas()
            ref = args.references or args.reference or args.reference_image
            editor.submit_video_prompt(args.prompt, duration=args.duration, resolution=args.resolution, aspect_ratio=args.ratio, reference=ref)
            success = editor.wait_for_video_generation(timeout=args.timeout)
            if not success:
                print(json.dumps({"success": False, "error": "Timeout na renderização do vídeo"}))
                sys.exit(1)

            saved_file = downloader.download_video(resolution=args.resolution, filename=args.filename)
            abs_saved_file = os.path.abspath(saved_file) if saved_file else None
            abs_output_dir = os.path.abspath(client.download_dir) if client.download_dir else None
            print(json.dumps({
                "success": True,
                "session": client.session,
                "model": "Omni 1.1 Flash",
                "duration": f"{args.duration}s",
                "ratio": args.ratio,
                "resolution": args.resolution,
                "reference": ref,
                "downloaded_file": abs_saved_file,
                "output_dir": abs_output_dir
            }, indent=2))

        elif args.command == "batch":
            client.ensure_canvas()
            ref = args.references or args.reference or args.reference_image

            if not os.path.exists(args.manifest):
                print(json.dumps({"success": False, "error": f"Arquivo de manifest não encontrado: {args.manifest}"}))
                sys.exit(1)

            with open(args.manifest, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)

            prompts = []
            filenames = []
            if isinstance(manifest_data, list):
                for i, item in enumerate(manifest_data):
                    if isinstance(item, str):
                        prompts.append({"slide": i + 1, "prompt": item})
                        filenames.append(f"slide_{i+1:02d}.jpeg")
                    elif isinstance(item, dict):
                        prompts.append(item)
                        filenames.append(item.get("filename") or f"slide_{item.get('slide', i+1):02d}.jpeg")
            elif isinstance(manifest_data, dict) and "slides" in manifest_data:
                for i, item in enumerate(manifest_data["slides"]):
                    prompts.append(item)
                    filenames.append(item.get("filename") or f"slide_{item.get('slide', i+1):02d}.jpeg")
            else:
                print(json.dumps({"success": False, "error": "Formato de manifest inválido. Deve ser uma lista de prompts ou um dict com 'slides'."}))
                sys.exit(1)

            log(f"[FlowCLI] Iniciando lote concorrente com {len(prompts)} slides (delay de {args.delay}s por prompt)...")
            submitted = editor.submit_batch_concurrent(
                prompts,
                model=args.model,
                aspect_ratio=args.ratio,
                reference=ref,
                delay_between=args.delay
            )

            success = editor.wait_for_batch_completion(expected_count=len(submitted), timeout=args.timeout)
            if not success:
                print(json.dumps({"success": False, "error": "Timeout na renderização concorrente do lote"}))
                sys.exit(1)

            downloaded = downloader.download_batch(
                count=len(submitted),
                filenames=filenames,
                resolution=args.resolution
            )

            abs_downloaded = [os.path.abspath(f) for f in downloaded]
            abs_output_dir = os.path.abspath(client.download_dir) if client.download_dir else None
            print(json.dumps({
                "success": True,
                "session": client.session,
                "type": "batch",
                "total_slides": len(abs_downloaded),
                "model": args.model,
                "ratio": args.ratio,
                "reference": ref,
                "downloaded_files": abs_downloaded,
                "output_dir": abs_output_dir
            }, indent=2))

        elif args.command == "download-all":
            files = downloader.download_all_rail(resolution=args.resolution, max_items=args.count)
            abs_files = [os.path.abspath(f) for f in files]
            abs_output_dir = os.path.abspath(client.download_dir) if client.download_dir else None
            print(json.dumps({
                "success": True,
                "downloaded_count": len(abs_files),
                "files": abs_files,
                "output_dir": abs_output_dir
            }, indent=2))

    finally:
        client.close()

if __name__ == "__main__":
    main()
