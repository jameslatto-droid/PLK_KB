"""
Indexing worker entry point.

This module is executed as a worker, not a service.
"""


def main():
    raise RuntimeError(
        "Indexing module skeleton only. "
        "No runtime behaviour defined at Stage 2."
    )


if __name__ == "__main__":
    main()
