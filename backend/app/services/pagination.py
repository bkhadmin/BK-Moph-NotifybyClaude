def paginate(items:list, page:int=1, per_page:int=20):
    page = max(page or 1, 1)
    per_page = max(min(per_page or 20, 100), 1)
    total = len(items)
    pages = max((total + per_page - 1) // per_page, 1)
    if page > pages:
        page = pages
    start = (page - 1) * per_page
    end = start + per_page
    return {
        "items": items[start:end],
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
        "has_prev": page > 1,
        "has_next": page < pages,
    }
