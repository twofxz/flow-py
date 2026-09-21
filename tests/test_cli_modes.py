import pytest
from flow_api.cli import build_parser

def test_cli_parser_defaults_to_headless():
    parser = build_parser()
    
    # generate command defaults to head=False (headless=True)
    args_gen = parser.parse_args(["generate", "--prompt", "A test prompt"])
    assert getattr(args_gen, "head", False) is False
    
    # generate with --head flag
    args_gen_head = parser.parse_args(["generate", "--prompt", "A test prompt", "--head"])
    assert args_gen_head.head is True

def test_video_parser_head_flag():
    parser = build_parser()
    args_vid = parser.parse_args(["video", "--prompt", "test", "--duration", "4"])
    assert getattr(args_vid, "head", False) is False

    args_vid_head = parser.parse_args(["video", "--prompt", "test", "--duration", "4", "--head"])
    assert args_vid_head.head is True

def test_download_all_count_and_json_flags():
    parser = build_parser()
    args = parser.parse_args(["download-all", "--count", "5", "--json"])
    assert args.command == "download-all"
    assert args.count == 5
    assert args.json is True

def test_all_subcommands_support_json_flag():
    parser = build_parser()
    
    args_gen = parser.parse_args(["generate", "--prompt", "test", "--json"])
    assert args_gen.json is True

    args_vid = parser.parse_args(["video", "--prompt", "test", "--duration", "4", "--json"])
    assert args_vid.json is True

    args_batch = parser.parse_args(["batch", "--manifest", "manifest.json", "--json"])
    assert args_batch.json is True

def test_logger_writes_to_stderr_not_stdout(capsys):
    from flow_api.logger import log
    import sys
    log("This is an internal status message")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "This is an internal status message" in captured.err

