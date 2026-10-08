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
