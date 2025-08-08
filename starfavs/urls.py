from django.urls import path, include
from starfavs.user.presentation.urls import urlpatterns as user_urls
from starfavs.favorites.presentation.urls import urlpatterns as favorite_urls

urlpatterns = [
    path("api/users/", include(user_urls)),
    path("api/favorites/", include(favorite_urls)),
]
