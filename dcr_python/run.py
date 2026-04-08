#!/usr/bin/env python
"""
DCR 2000 Application Launcher
Run this file to start the application
"""

import sys
import os

# Ensure project root is on sys.path so `src` is importable as a package
src_path = os.path.join(os.path.dirname(__file__), 'src')
project_root = os.path.dirname(src_path)
sys.path.insert(0, project_root)

from src.main import main

if __name__ == "__main__":
    main()
