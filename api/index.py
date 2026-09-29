import os
import sys
from pathlib import Path

# Add project root and backend directory to python path for Vercel
ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"

for path in [str(ROOT), str(BACKEND)]:
    if path not in sys.path:
        sys.path.insert(0, path)

from backend.app.main import app
