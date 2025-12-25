import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from .pipeline import index_all_chunks


def main(argv=None):
    parser = argparse.ArgumentParser(description="Lexical index rebuild")
    parser.add_argument("command", choices=["rebuild"], help="Rebuild index")
    args = parser.parse_args(argv)

    if args.command == "rebuild":
        count = index_all_chunks()
        print(f"Indexed chunks: {count}")


if __name__ == "__main__":
    main()
