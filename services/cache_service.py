"""
Cache management for Finder.fi data
"""
import json
import os


def load_finder_cache():
    """Load Finder.fi cache from file"""
    cache_file = 'finder_cache.json'
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_finder_cache(cache):
    """Save Finder.fi cache to file"""
    cache_file = 'finder_cache.json'
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving cache: {e}")
        