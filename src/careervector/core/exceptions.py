class LLMResponseError(RuntimeError):
    """Raised when an LLM call doesn't return usable output (e.g. no tool call emitted)."""
