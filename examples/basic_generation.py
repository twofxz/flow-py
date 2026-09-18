from flow_api import FlowClient, FlowEditor, FlowDownloader

client = FlowClient()
page = client.connect()

try:
    editor = FlowEditor(page)
    editor.submit_prompt(
        prompt="Photoreal cinematic shot of an ancient Kyoto temple surrounded by cherry blossoms in morning mist...",
        model="Nano Banana 2",
        aspect_ratio="16:9"
    )
    editor.wait_for_generation()

    downloader = FlowDownloader(page, client.download_dir)
    img_path = downloader.download_current(resolution="1K")
    print(f"Downloaded: {img_path}")
finally:
    client.close()
