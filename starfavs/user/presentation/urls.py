from django.urls import path
from . import views

urlpatterns = [
    path("", views.list_users, name="user-list"),
    path("create/", views.create_user, name="user-create"),
    path("<int:user_id>/", views.get_user, name="user-detail"),
    path("<int:user_id>/delete/", views.delete_user, name="user-delete"),
]
