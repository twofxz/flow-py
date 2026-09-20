import pytest
from flow_api.client import FlowClient

def test_stop_background_process_method_exists():
    client = FlowClient()
    assert hasattr(client, "stop_background_process")
    # Calling it when stopped should safely return boolean without crashing
    result = client.stop_background_process()
    assert isinstance(result, bool)
