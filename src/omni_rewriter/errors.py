"""Explicit exception hierarchy for backend, media, and agent failures."""


class OmniRewriterError(Exception):
    """Base class for all operational Omni-Rewriter errors."""


class BackendError(OmniRewriterError):
    """The language-model backend failed."""


class BackendConfigurationError(BackendError):
    """The backend configuration is invalid."""


class BackendTransportError(BackendError):
    """The backend could not be reached after retrying."""


class BackendResponseError(BackendError):
    """The backend returned an invalid or unsuccessful response."""


class MediaError(OmniRewriterError):
    """A media input could not be accepted."""


class MediaURIError(MediaError):
    """A media URI is unsupported or unsafe."""


class MediaTooLargeError(MediaError):
    """A media asset exceeds the configured byte limit."""


class MediaMIMEError(MediaError):
    """A media asset has an absent, unsupported, or mismatched MIME type."""


class AgentError(OmniRewriterError):
    """The rewrite agent failed."""


class StructuredOutputError(AgentError):
    """An LLM response did not contain valid structured JSON."""


class RepairExhaustedError(AgentError):
    """The bounded validation and repair loop was exhausted."""
