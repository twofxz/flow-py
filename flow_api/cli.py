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
    gen_parser.add_argument("--ratio", type=str, default="16:9", help="Proporção da imagem (16:9, 9:16, 1:1, 3:4)")
    gen_parser.add_argument("--output-dir", type=str, default=None, help="Pasta de destino dos arquivos")
    gen_parser.add_argument("--resolution", type=str, default="1K", choices=["1K", "2K"], help="Resolução nativa de download")
    gen_parser.add_argument("--timeout", type=int, default=90, help="Tempo limite de geração em segundos")

    # Comando: video
    vid_parser = subparsers.add_parser("video", help="Gera vídeos no Google Flow usando Gemini Omni Flash 1.1")
    vid_parser.add_argument("--prompt", type=str, required=True, help="Prompt textual do vídeo")
    vid_parser.add_argument("--duration", type=int, required=True, choices=[4, 6, 8, 10], help="Duração OBRIGATÓRIA do vídeo em segundos (4, 6, 8 ou 10)")
    vid_parser.add_argument("--reference", type=str, default=None, help="Nome do arquivo na biblioteca ou caminho da imagem local para I2V")
    vid_parser.add_argument("--reference-image", type=str, default=None, help="Alias para caminho da imagem de referência local")
    vid_parser.add_argument("--filename", type=str, default=None, help="Nome personalizado do vídeo salvo (ex: meu_video.mp4)")
    vid_parser.add_argument("--ratio", type=str, default="16:9", choices=["16:9", "9:16"], help="Proporção do vídeo (16:9 ou 9:16)")
    vid_parser.add_argument("--resolution", type=str, default="720p", choices=["720p"], help="Resolução do vídeo (estritamente 720p)")
    vid_parser.add_argument("--output-dir", type=str, default=None, help="Pasta de destino dos arquivos")
    vid_parser.add_argument("--timeout", type=int, default=180, help="Tempo limite de geração em segundos")

    # Comando: batch (geração concorrente rápida - 3s delay)
    batch_parser = subparsers.add_parser("batch", help="Gera múltiplos slides concorrentemente (delay inteligente de 3s por prompt)")
    batch_parser.add_argument("--manifest", type=str, required=True, help="Caminho do arquivo JSON com os prompts")
    batch_parser.add_argument("--reference", type=str, default=None, help="Nome do arquivo de referência na biblioteca ou caminho local")
    batch_parser.add_argument("--reference-image", type=str, default=None, help="Alias para caminho local da referência")
    batch_parser.add_argument("--model", type=str, default="Nano Banana 2", choices=["Nano Banana 2", "Nano Banana Pro"], help="Modelo de imagem")
    batch_parser.add_argument("--ratio", type=str, default="3:4", help="Proporção da imagem (3:4, 16:9, 9:16, 1:1)")
    batch_parser.add_argument("--delay", type=float, default=3.0, help="Intervalo em segundos entre envios (padrão: 3.0s)")
    batch_parser.add_argument("--output-dir", type=str, default=None, help="Pasta de destino dos arquivos")
    batch_parser.add_argument("--resolution", type=str, default="1K", choices=["1K", "2K"], help="Resolução de download")
    batch_parser.add_argument("--timeout", type=int, default=180, help="Tempo limite total de renderização do lote")

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

        elif args.command == "video":
            client.ensure_canvas()
            ref = args.reference or args.reference_image
            editor.submit_video_prompt(args.prompt, duration=args.duration, resolution=args.resolution, aspect_ratio=args.ratio, reference=ref)
            success = editor.wait_for_video_generation(timeout=args.timeout)
            if not success:
                print(json.dumps({"success": False, "error": "Timeout na renderização do vídeo"}))
                sys.exit(1)

            saved_file = downloader.download_video(resolution=args.resolution, filename=args.filename)
            print(json.dumps({
                "success": True,
                "model": "Omni 1.1 Flash",
                "duration": f"{args.duration}s",
                "ratio": args.ratio,
                "resolution": args.resolution,
                "reference": ref,
                "downloaded_file": saved_file,
                "output_dir": client.download_dir
            }, indent=2))

        elif args.command == "batch":
            client.ensure_canvas()
            ref = args.reference or args.reference_image

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

            print(f"[FlowCLI] Iniciando lote concorrente com {len(prompts)} slides (delay de {args.delay}s por prompt)...")
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

            print(json.dumps({
                "success": True,
                "type": "batch",
                "total_slides": len(downloaded),
                "model": args.model,
                "ratio": args.ratio,
                "reference": ref,
                "downloaded_files": downloaded,
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
