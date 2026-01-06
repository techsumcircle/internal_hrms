from django.urls import include, path
# from .authentication import urlpatterns as all_urls
from .employee_urls import urlpatterns as employee_urls
# from .reports import urlpatterns as reports_urls

urlpatterns = [
    # path('', include(all_urls)),
    *employee_urls,
]