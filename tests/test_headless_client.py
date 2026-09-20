import pytest
from flow_api.client import FlowClient

def test_headless_flags_configuration():
    client_headless = FlowClient(headless=True)
    assert client_headless.headless is True

    client_visible = FlowClient(headless=False)
    assert client_visible.headless is False
