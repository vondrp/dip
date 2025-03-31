# core/__init__.py

import sys
import os

# Tento kód by mohl být použit pro nastavení sys.path, pokud je potřeba
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'profiler_tool')))
