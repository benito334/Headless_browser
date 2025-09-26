import sys, pathlib, os
# Ensure project root is on sys.path for container execution
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
