"""
CLI do Motor Google Flow
Interface unificada para execução rápida via terminal e integração nativa com Antigravity.
"""

import sys
import argparse
import json
from .client import FlowClient
from .editor import FlowEditor
from .downloader import FlowDownloader

def main():
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="Google Flow Automation Engine CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Comando: generate
    gen_parser = subparsers.add_parser("generate", help="Gera imagens no Google Flow e realiza download nativo")
    gen_parser.add_argument("--prompt", type=str, required=True, help="Prompt textual da imagem")
    gen_parser.add_argument("--reference", type=str, default=None, help="Nome do arquivo na biblioteca ou caminho da imagem local")
    gen_parser.add_argument("--reference-image", type=str, default=None, help="Alias para caminho da imagem de referência local")
    gen_parser.add_argument("--filename", type=str, default=None, help="Nome personalizado do arquivo salvo (ex: meu_personagem.jpeg)")
    gen_parser.add_argument("--model", type=str, default="Nano Banana 2", help="Modelo de geração")
    gen_parser.add_argument("--ratio", type=str, default="16:9", help="Proporção da imagem (16:9, 9:16, 1:1)")
    gen_parser.add_argument("--output-dir", type=str, default=None, help="Pasta de destino dos arquivos")
    gen_parser.add_argument("--resolution", type=str, default="1K", choices=["1K", "2K"], help="Resolução nativa de download")
    gen_parser.add_argument("--timeout", type=int, default=90, help="Tempo limite de geração em segundos")

    # Comando: download-all
    dl_parser = subparsers.add_parser("download-all", help="Baixa todas as imagens da galeria ativa")
    dl_parser.add_argument("--output-dir", type=str, default=None, help="Pasta de destino dos arquivos")
    dl_parser.add_argument("--resolution", type=str, default="1K", choices=["1K", "2K"], help="Resolução de download")
    dl_parser.add_argument("--count", type=int, default=None, help="Número máximo de imagens a baixar")

    args = parser.parse_args()
    client = FlowClient(download_dir=args.output_dir)

    try:
        page = client.connect()
        editor = FlowEditor(page)
        downloader = FlowDownloader(page, client.download_dir)

        if args.command == "generate":
            client.ensure_canvas()
            ref = args.reference or args.reference_image
            editor.submit_prompt(args.prompt, model=args.model, aspect_ratio=args.ratio, reference=ref)
            success = editor.wait_for_generation(timeout=args.timeout)
            if not success:
                print(json.dumps({"success": False, "error": "Timeout na renderização"}))
                sys.exit(1)

            downloader.open_viewer()
            saved_file = downloader.download_current(resolution=args.resolution, filename=args.filename)
            print(json.dumps({
                "success": True,
                "model": args.model,
                "ratio": args.ratio,
                "reference": ref,
                "downloaded_file": saved_file,
                "output_dir": client.download_dir
            }, indent=2))

        elif args.command == "download-all":
            files = downloader.download_all_rail(resolution=args.resolution, max_items=args.count)
            print(json.dumps({
                "success": True,
                "downloaded_count": len(files),
                "files": files
            }, indent=2))

    finally:
        client.close()

if __name__ == "__main__":
    main()
