from django.contrib import admin
from django.urls import path, include
from starfavs.urls import urlpatterns as starfavs_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(starfavs_urls)),
]
