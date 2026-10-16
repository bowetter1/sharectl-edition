import sys

from .cli import main

try:
    sys.exit(main())
except (ValueError, OSError) as exc:
    print(f"Error: {exc}", file=sys.stderr)
    sys.exit(1)
