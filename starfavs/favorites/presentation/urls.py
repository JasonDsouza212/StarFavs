from django.urls import path
from . import views

urlpatterns = [
    # Handle GET, POST, DELETE requests for favorites.
    path("", views.favorites_handler, name="favorites-handler"),
    # Handle PUT and DELETE requests for a favorite by ID.
    path("<int:favorite_id>/", views.manage_favorite, name="favorites-manage"),
    # List content with customizations
    path(
        "content/<str:record_type>/",
        views.list_content_with_customizations,
        name="content-list",
    ),
]
