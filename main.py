#!/usr/bin/env python3
"""Entry point for FGO Craft Essence Auto Enhancement Tool"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fgo_auto_enhance.main_app import main

if __name__ == "__main__":
    main()