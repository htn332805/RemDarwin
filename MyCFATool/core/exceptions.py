class MyCFAToolError(Exception):
    """Base exception for MyCFATool."""
    pass


class DatabaseError(MyCFAToolError):
    """Raised when database operations fail."""
    pass


class DataNotFoundError(MyCFAToolError):
    """Raised when requested data is not found."""
    pass


class ConfigurationError(MyCFAToolError):
    """Raised when configuration is invalid."""
    pass


class DataIngestionError(MyCFAToolError):
    """Raised when data ingestion operations fail."""
    pass