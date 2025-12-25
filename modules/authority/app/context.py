from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class AuthorityContext:
    user: str
    roles: List[str] = field(default_factory=list)
    project_codes: List[str] = field(default_factory=list)
    discipline: str = "general"
    classification: Optional[str] = None
    commercial_sensitivity: Optional[str] = None
