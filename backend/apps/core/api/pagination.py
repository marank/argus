from ninja.pagination import PageNumberPagination


class Pagination(PageNumberPagination):
    """Page number pagination returning ``{"items": [...], "count": n}``."""

    def __init__(self, **kwargs):
        kwargs.setdefault("page_size", 25)
        kwargs.setdefault("max_page_size", 500)
        super().__init__(**kwargs)
