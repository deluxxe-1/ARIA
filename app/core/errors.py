class ARIAError(Exception):
    pass


class WorkspaceBoundaryError(ARIAError):
    pass


class ProfileNotFoundError(ARIAError):
    pass


class ToolNotSupportedError(ARIAError):
    pass


class VoiceBackendError(ARIAError):
    pass


class UploadTooLargeError(ARIAError):
    pass


class InvalidUploadError(ARIAError):
    pass


class UnauthorizedError(ARIAError):
    pass


class RateLimitError(ARIAError):
    pass
