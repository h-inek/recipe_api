from rest_framework.pagination import PageNumberPagination

from foodgram.constants import MAX_PAGE_SIZE


class CustomPagination(PageNumberPagination):
    """Кастомный паджинатор с изменением полей на page и limit"""
    page_query_param = 'page'
    page_size_query_param = 'limit'
    max_page_size = MAX_PAGE_SIZE
