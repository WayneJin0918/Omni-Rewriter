"""Omni-Writer public API."""

from .agent import (
    AgentState,
    AnalysisPlan,
    RewriteAgent,
    RewriteAgentConfig,
    RewriteResult,
)
from .adapters import H3Client, H3ClientConfig, MiniMaxClient, MiniMaxClientConfig
from .backends import (
    ChatBackend,
    ChatBackendConfig,
    FakeBackend,
    OpenAICompatibleBackend,
    ScriptedBackend,
)
from .config import Settings
from .evaluator import BasicEvaluator, Evaluator
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
    OmniWriterError,
    RepairExhaustedError,
    StructuredOutputError,
)
from .media_input import MediaInputConfig, MediaPreparer, PreparedMedia
from .models import (
    BaseRewrite,
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
    "OmniWriterError",
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
