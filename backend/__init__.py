import sys
import types
import importlib
from pathlib import Path

# Ensure project root is on sys.path so that absolute imports work correctly when
# the package is executed inside the Docker container.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# ---------------------------------------------------------------------------
# Backwards-compatibility layer
# ---------------------------------------------------------------------------
# The codebase previously lived inside a top-level package called `src`.  To avoid
# modifying the internal logic of `instagram_scraper.py` (which still performs
# imports such as `from src.config import …`) we create a lightweight shim
# package at runtime that forwards those legacy import paths to the new
# locations under `backend.*`.
#
#   src                → backend (this actual package)
#   src.config         → backend.config
#   src.db             → backend.db
#   src.instagram_scraper → backend.ingestion.instagram_ingestion.instagram_scraper
#
# NOTE:  This shim must be established as early as possible so that any
#        downstream modules can safely `import src.…` without changes.
# ---------------------------------------------------------------------------
legacy_pkg = types.ModuleType("src")

# Map sub-modules one by one.  Using importlib allows the real modules to be
# lazily imported only when first accessed.
legacy_pkg.config = importlib.import_module("backend.config")
legacy_pkg.db = importlib.import_module("backend.db.db")
legacy_pkg.instagram_scraper = importlib.import_module(
    "backend.ingestion.instagram_ingestion.instagram_scraper")

# Expose attributes for `from src import X` style imports.
for name in ("config", "db", "instagram_scraper"):
    setattr(legacy_pkg, name, getattr(legacy_pkg, name))

# Finally register the shim in sys.modules under both the top-level name and the
# fully-qualified sub-module names expected by legacy code.
sys.modules.setdefault("src", legacy_pkg)
sys.modules["src.config"] = legacy_pkg.config
sys.modules["src.db"] = legacy_pkg.db
sys.modules["src.instagram_scraper"] = legacy_pkg.instagram_scraper
