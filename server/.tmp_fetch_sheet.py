import os
import sys
# Garante que o diretório raiz do projeto esteja no PYTHONPATH
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from server.integrations.google_knowledge import fetch_sheet_catalog
from server.config import GOOGLE_SHEET_ID, GOOGLE_SHEET_RANGE
import json

if __name__ == '__main__':
    res = fetch_sheet_catalog(GOOGLE_SHEET_ID, GOOGLE_SHEET_RANGE, max_items=50)
    print(json.dumps(res, ensure_ascii=False, indent=2))
