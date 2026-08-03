"""Video generation service adapters."""

from .h3 import H3Client, H3ClientConfig
from .minimax import MiniMaxClient, MiniMaxClientConfig

__all__ = ["H3Client", "H3ClientConfig", "MiniMaxClient", "MiniMaxClientConfig"]
