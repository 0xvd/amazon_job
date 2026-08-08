from pathlib import Path
import json
import os
import sys

if sys.platform == 'win32':
    cache_path = Path(os.environ['LOCALAPPDATA'])
else:
    cache_path = Path.home() / '.cache'

CACHE_DIR = cache_path / 'amazon_tool'
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def save_cache(section, data):
    with (CACHE_DIR / f'{section}.json').open('w', encoding='utf-8') as f:
        json.dump({
            'stored_by': 'amazon_tool',
            'data': data,
        }, f, indent=2)

def load_cache(section, default=None):
    try:
        with (CACHE_DIR / f'{section}.json').open('r', encoding='utf-8') as f:
            return json.load(f)['data']
    except Exception:
        return default