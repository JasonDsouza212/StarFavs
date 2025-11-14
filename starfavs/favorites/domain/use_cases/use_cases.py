# starfavs/favorites/domain/use_cases/use_cases.py
"""Application use cases for favorites and content listing."""

from typing import List
from starfavs.favorites.data.db_repository import FavoriteRepository
from starfavs.favorites.data.content_service import ContentService
from starfavs.favorites.domain.models import Favorite
from starfavs.favorites.presentation.types import (
    CreateFavoriteInput,
    UpdateFavoriteInput,
    DeleteFavoriteByIdInput,
    DeleteUserFavoritesByTypeInput,
    GetUserFavoritesInput,
    ListContentInput,
    ContentListResponse,
)


class CreateFavoriteUC:
    """Create a new favorite for a user."""

    def __init__(self, repo: FavoriteRepository):
        self.repo = repo

    def execute(self, input: CreateFavoriteInput) -> Favorite:
        """Create the favorite.

        Raises:
            ValueError: If favorite exists or creation fails.
        """
        if self.repo.favorite_exists(
            input.user_id, input.external_record_id, input.record_type
        ):
            raise ValueError("Favorite already exists for this user and record")
        fav = self.repo.create_favorite(
            user_id=input.user_id,
            custom_title=input.custom_title,
            original_name=input.original_name,
            external_record_id=input.external_record_id,
            record_type=input.record_type,
        )
        if not fav:
            raise ValueError("Failed to create favorite")
        return fav


class UpdateFavoriteUC:
    """Update a favorite's custom title."""

    def __init__(self, repo: FavoriteRepository):
        self.repo = repo

    def execute(self, input: UpdateFavoriteInput) -> Favorite:
        """Update the custom title.

        Raises:
            ValueError: If favorite not found.
        """
        fav = self.repo.update_favorite_title(
            input.favorite_id, input.custom_title or ""
        )
        if not fav:
            raise ValueError("Favorite not found")
        return fav


class DeleteFavoriteByIdUC:
    """Delete a favorite by ID."""

    def __init__(self, repo: FavoriteRepository):
        self.repo = repo

    def execute(self, input: DeleteFavoriteByIdInput) -> bool:
        return self.repo.delete_favorites(favorite_id=input.favorite_id)


class DeleteUserFavoritesByTypeUC:
    """Delete one or many favorites for a user by type (and optional external id)."""

    def __init__(self, repo: FavoriteRepository):
        self.repo = repo

    def execute(self, input: DeleteUserFavoritesByTypeInput) -> bool:
        return self.repo.delete_favorites(
            user_id=input.user_id,
            record_type=input.record_type,
            external_record_id=input.external_record_id,
        )


class GetUserFavoritesUC:
    """List a user's favorites, optionally filtered by record type."""

    def __init__(self, repo: FavoriteRepository):
        self.repo = repo

    def execute(self, input: GetUserFavoritesInput) -> List[Favorite]:
        return self.repo.get_user_favorites(
            user_id=input.user_id, record_type=input.record_type
        ).get("favorites")


class ListContentWithCustomizationsUC:
    """List content (movies/planets) decorated with user's custom titles + flags."""

    def __init__(self, content_service: ContentService):
        self.content_service = content_service

    def execute(self, input: ListContentInput) -> ContentListResponse:
        """List content for a given record type for a user"""

        return self.content_service.get_content_with_custom_names(
            user_id=input.user_id,
            page=input.page,
            limit=input.limit,
            search=input.search,
            record_type=input.record_type,
        )
