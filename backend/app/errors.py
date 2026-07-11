class AppError(Exception):
    code = "application_error"

    def __init__(self, message: str, detail: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail


class ParseError(AppError):
    code = "parse_failed"


class LLMError(AppError):
    code = "llm_failed"


class InvalidStateError(AppError):
    code = "invalid_state"

