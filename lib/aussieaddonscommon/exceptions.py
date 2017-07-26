class AussieAddonsNonFatalException(Exception):
    """A custom non-fatal exception

    This exception can be thrown when catching other exceptions, and it will
    be explicitly ignored from automatic error reports
    """
    pass
