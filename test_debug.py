#!/usr/bin/env python3
"""
Debug test script with detailed logging
"""

import logging
import sys

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Import and run main
from fgo_auto_enhance.main_app import FGOAutoEnhanceApp

if __name__ == "__main__":
    app = FGOAutoEnhanceApp()
    app.run(target_level=2, max_attempts=1)