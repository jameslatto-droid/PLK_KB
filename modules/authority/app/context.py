from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class AuthorityContext:
    user: str
    roles: List[str]
    project_codes: List[str]
    discipline: str
