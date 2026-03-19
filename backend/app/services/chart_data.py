from collections import Counter

def counter_from_rows(rows:list[dict], key:str):
    c = Counter()
    for row in rows:
        c[str(row.get(key) or 'unknown')] += 1
    return dict(c)
