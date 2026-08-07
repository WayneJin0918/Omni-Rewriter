"""Optional online and local generation adapters."""

from .base import (
    GenerationAdapterError,
    GenerationConfigurationError,
    GenerationResponseError,
    GenerationTooLargeError,
    GenerationTransportError,
    ImageGeneratorAdapter,
    VideoGeneratorAdapter,
)
from .h3 import H3Client, H3ClientConfig
from .hunyuan_image import HunyuanImageVLLMClient, HunyuanImageVLLMClientConfig
from .lingbot_rewriter import (
    LingBotRewriterClient,
    LingBotRewriterConfig,
    LingBotRewriteResult,
)
from .lingbot_runner import (
    LingBotVideoOptions,
    LingBotVideoResult,
    LingBotVideoRunner,
)
from .minimax import MiniMaxClient, MiniMaxClientConfig
from .omni_videos import OmniVideosClient, OmniVideosClientConfig, WanOmniAdapter
from .openai_images import OpenAIImagesClient, OpenAIImagesClientConfig

__all__ = [
    "GenerationAdapterError",
    "GenerationConfigurationError",
    "GenerationResponseError",
    "GenerationTooLargeError",
    "GenerationTransportError",
    "H3Client",
    "H3ClientConfig",
    "HunyuanImageVLLMClient",
    "HunyuanImageVLLMClientConfig",
    "ImageGeneratorAdapter",
    "LingBotRewriteResult",
    "LingBotRewriterClient",
    "LingBotRewriterConfig",
    "LingBotVideoOptions",
    "LingBotVideoResult",
    "LingBotVideoRunner",
    "MiniMaxClient",
    "MiniMaxClientConfig",
    "OmniVideosClient",
    "OmniVideosClientConfig",
    "OpenAIImagesClient",
    "OpenAIImagesClientConfig",
    "VideoGeneratorAdapter",
    "WanOmniAdapter",
]
