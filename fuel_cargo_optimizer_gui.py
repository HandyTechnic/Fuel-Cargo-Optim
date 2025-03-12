#!/usr/bin/env python3
"""
Fuel and Cargo Optimization GUI Launcher

This is the main entry point for the graphical user interface of the
fuel and cargo optimization system. It launches the GUI application.
"""
import os
import sys

# Add the project root to the Python path to ensure imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Launching Fuel-Cargo Optimization GUI... A window should appear shortly.")

from src.gui.app import main

if __name__ == "__main__":
    main()