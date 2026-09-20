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
