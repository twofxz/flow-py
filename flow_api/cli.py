"""
CLI Oficial do google-flow-api
"""

import sys
import argparse
import json
import time

from .client import FlowClient, FLOW_BASE_URL
from .editor import FlowEditor
from .downloader import FlowDownloader

def main():
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        prog="flow",
        description="Google Flow Automation API & CLI"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # flow login
    login_parser = subparsers.add_parser("login", help="Abre o navegador para autenticar a conta Google")

    # flow generate
    gen_parser = subparsers.add_parser("generate", help="Gera imagem no Google Flow")
    gen_parser.add_argument("--prompt", type=str, required=True, help="Prompt da imagem")
    gen_parser.add_argument("--model", type=str, default="Nano Banana 2", help="Modelo (Nano Banana 2)")
    gen_parser.add_argument("--ratio", type=str, default="16:9", choices=["16:9", "9:16", "1:1", "4:3", "3:4"])
    gen_parser.add_argument("--output-dir", type=str, default=None, help="Pasta de saída")
    gen_parser.add_argument("--resolution", type=str, default="1K", choices=["1K", "2K"])

    # flow serve
    serve_parser = subparsers.add_parser("serve", help="Inicia servidor local compatível com OpenAI")
    serve_parser.add_argument("--port", type=int, default=8000, help="Porta do servidor")

    args = parser.parse_args()

    if args.command == "login":
        client = FlowClient()
        print("Iniciando navegador para login no Google Flow...")
        client.launch_browser_process(headless=False)
        print("Faça o login na janela aberta. O perfil será salvo automaticamente.")
        return

    elif args.command == "generate":
        client = FlowClient(download_dir=args.output_dir)
        try:
            page = client.connect()
            client.ensure_canvas()
            editor = FlowEditor(page)
            downloader = FlowDownloader(page, client.download_dir)

            editor.submit_prompt(args.prompt, model=args.model, aspect_ratio=args.ratio)
            success = editor.wait_for_generation(timeout=90)
            if not success:
                print(json.dumps({"success": False, "error": "Timeout na renderização"}))
                sys.exit(1)

            file_path = downloader.download_current(resolution=args.resolution)
            print(json.dumps({
                "success": True,
                "model": args.model,
                "ratio": args.ratio,
                "resolution": args.resolution,
                "file": file_path
            }, indent=2))
        finally:
            client.close()

    elif args.command == "serve":
        import uvicorn
        from .server import app
        print(f"Iniciando servidor OpenAI-Compatible em http://127.0.0.1:{args.port}")
        uvicorn.run(app, host="127.0.0.1", port=args.port)

if __name__ == "__main__":
    main()
