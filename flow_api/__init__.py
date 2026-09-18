"""
Google Flow Automation Engine
Pacote modular em Python para controle, geração e download nativo de mídias no Google Flow.
"""

from .client import FlowClient
from .editor import FlowEditor
from .downloader import FlowDownloader

__all__ = ["FlowClient", "FlowEditor", "FlowDownloader"]
__version__ = "1.0.0"
