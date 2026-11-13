# tests/conftest.py
import os
import sys
from pathlib import Path

# Adiciona a raiz do repositório ao PYTHONPATH automaticamente
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("GROQ_API_KEY", "mock_groq_key_for_ci")
os.environ.setdefault("API_KEY", "mock_api_key_for_ci")