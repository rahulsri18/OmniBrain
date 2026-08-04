class GuardrailViolation(Exception):
    """
    Raised when a user's request is blocked
    by the application's guardrails.
    """

    def __init__(self, message: str = "Request blocked by guardrails."):
        self.message = message
        super().__init__(self.message)