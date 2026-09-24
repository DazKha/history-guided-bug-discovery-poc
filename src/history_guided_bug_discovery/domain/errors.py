class DiscoveryEngineError(Exception):
    """Base error for typed discovery-engine failures."""


class SchemaValidationError(DiscoveryEngineError, ValueError):
    pass


class ConfigurationError(DiscoveryEngineError, ValueError):
    pass


class ArtifactError(DiscoveryEngineError):
    pass
