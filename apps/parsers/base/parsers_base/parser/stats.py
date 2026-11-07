from dataclasses import dataclass


@dataclass
class ParserStats:
    extracted: int = 0
    valid: int = 0
    invalid: int = 0
    inserted: int = 0
    ignored: int = 0
