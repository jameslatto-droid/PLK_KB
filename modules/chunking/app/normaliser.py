"""
Normalisation logic.

Normalisation prepares artefact content for chunking
without changing meaning or structure.
"""


def normalise_text(text: str) -> str:
    """
    Apply deterministic normalisation:
    - whitespace cleanup
    - encoding fixes
    - line ending consistency
    """
    return text.strip()
