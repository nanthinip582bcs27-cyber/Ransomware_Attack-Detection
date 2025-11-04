import os, math
from collections import Counter
def get_extension(path): return os.path.splitext(path)[1].lstrip('.').lower()
def sample_non_printable_pct(path, sample_bytes=1024):
    try:
        with open(path, 'rb') as f: b = f.read(sample_bytes)
        if not b: return 0.0
        np = sum(1 for x in b if x < 32 or x > 126)
        return round(100.0*np/len(b), 2)
    except Exception: return 0.0
def pseudo_entropy_from_bytes(b):
    if not b: return 0.0
    from collections import Counter
    c = Counter(b); t = len(b); e = 0.0
    for v in c.values(): p = v/t; e -= p*math.log2(p)
    return round(min(8.0,e),3)
def file_size_kb(path):
    try: return round(os.path.getsize(path)/1024.0,3)
    except Exception: return 0.0
