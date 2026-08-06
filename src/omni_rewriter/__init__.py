"""Omni-Rewriter public API."""

from .adapters import H3Client, H3ClientConfig, MiniMaxClient, MiniMaxClientConfig
from .agent import (
    AgentState,
    AnalysisPlan,
    RewriteAgent,
    RewriteAgentConfig,
    RewriteResult,
)
from .backends import (
    ChatBackend,
    ChatBackendConfig,
    FakeBackend,
    OpenAICompatibleBackend,
    ScriptedBackend,
)
from .config import Settings
from .errors import (
    AgentError,
    BackendConfigurationError,
    BackendError,
    BackendResponseError,
    BackendTransportError,
    MediaError,
    MediaMIMEError,
    MediaTooLargeError,
    MediaURIError,
    OmniRewriterError,
    RepairExhaustedError,
    StructuredOutputError,
)
from .evaluator import BasicEvaluator, Evaluator
from .media_input import MediaInputConfig, MediaPreparer, PreparedMedia
from .models import (
    BaseRewrite,
    ImagePEProfile,
    ImageRewrite,
    MediaReference,
    MediaRole,
    MediaType,
    Ref2VARewrite,
    RewriteOutput,
    RewriteRequest,
    TaskType,
    infer_task,
)
from .render import H3Renderable, render_h3_prompt
from .trace import JSONLTrace, redact

__all__ = [
    "AgentError",
    "AgentState",
    "AnalysisPlan",
    "BaseRewrite",
    "BackendConfigurationError",
    "BackendError",
    "BackendResponseError",
    "BackendTransportError",
    "BasicEvaluator",
    "ChatBackend",
    "ChatBackendConfig",
    "FakeBackend",
    "H3Client",
    "H3ClientConfig",
    "H3Renderable",
    "ImagePEProfile",
    "ImageRewrite",
    "JSONLTrace",
    "MediaError",
    "MediaInputConfig",
    "MediaMIMEError",
    "MediaPreparer",
    "MediaReference",
    "MediaRole",
    "MediaTooLargeError",
    "MediaType",
    "MediaURIError",
    "MiniMaxClient",
    "MiniMaxClientConfig",
    "OmniRewriterError",
    "OpenAICompatibleBackend",
    "PreparedMedia",
    "Ref2VARewrite",
    "RepairExhaustedError",
    "RewriteAgent",
    "RewriteAgentConfig",
    "RewriteOutput",
    "RewriteRequest",
    "RewriteResult",
    "ScriptedBackend",
    "Settings",
    "StructuredOutputError",
    "TaskType",
    "Evaluator",
    "infer_task",
    "redact",
    "render_h3_prompt",
]

__version__ = "0.1.0"
