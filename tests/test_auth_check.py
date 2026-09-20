import pytest
from unittest.mock import patch, MagicMock
from flow_api.cli import build_parser

def test_auth_check_parser():
    parser = build_parser()
    args = parser.parse_args(["auth-check"])
    assert args.command == "auth-check"
    assert getattr(args, "json", False) is False

    args_json = parser.parse_args(["auth-check", "--json"])
    assert args_json.command == "auth-check"
    assert args_json.json is True
