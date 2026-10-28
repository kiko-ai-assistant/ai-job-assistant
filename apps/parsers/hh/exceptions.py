class ScraperError(Exception):
    pass


class SourceBlockedError(ScraperError):
    pass


class CaptchaDetectedError(ScraperError):
    pass


class ParsingError(ScraperError):
    pass


class LayoutChangedError(ScraperError):
    pass


class MassFailureError(ScraperError):
    pass
