from django.core.paginator import Paginator
from django.conf import settings


def paginate_page(request, post_list):
    paginator = Paginator(post_list, settings.SORT_PAGES)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
