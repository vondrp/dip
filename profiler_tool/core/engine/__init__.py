import os
import sys

# Přidáme `core` do sys.path, aby `core.engine` šlo správně importovat
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
