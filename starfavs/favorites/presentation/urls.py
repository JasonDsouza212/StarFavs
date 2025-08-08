from django.urls import path
from . import views

urlpatterns = [
    path(
        "content/",
        views.list_content_with_customizations,
        name="list-content-with-customizations",
    ),
    path("", views.create_favorite, name="favorite-create"),
    path("<int:favorite_id>/", views.update_favorite, name="favorite-update"),
    path("<int:favorite_id>/delete/", views.delete_favorite, name="favorite-delete"),
    path("user/<int:user_id>/", views.get_user_favorites, name="user-favorites"),
    path(
        "user/<int:user_id>/type/<str:record_type>/",
        views.delete_user_favorites_by_type,
        name="delete-user-favorites-by-type",
    ),
    path(
        "user/<int:user_id>/type/<str:record_type>/favorite/<int:favorite_id>/",
        views.delete_user_favorite_by_id,
        name="delete-user-favorite-by-id",
    ),
]
