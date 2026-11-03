from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """
    ?page=2&page_size=24

    12 per page fits a 3- or 4-column product grid. The client may ask for more,
    but never more than 100, so nobody can pull the whole table in one request.
    """

    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 100
