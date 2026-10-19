class BusinessError(Exception):
    """A request that is valid in form but violates a business rule (HTTP 409)."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
