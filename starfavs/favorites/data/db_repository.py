from typing import Optional, List, Dict
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from starfavs.favorites.domain.models import Favorite
from starfavs.user.domain.models import User
from django.db.models import Q


class FavoriteRepository:
    """
    Repository for Favorite data access operations.
    """

    def create_favorite(
        self,
        user_id: int,
        custom_title: str | None,
        original_name: str,
        external_record_id: str,
        record_type: str,
    ) -> Optional[Favorite]:
        try:
            user = User.objects.get(id=user_id)
            favorite = Favorite.objects.create(
                user=user,
                custom_title=(custom_title or "").strip(),
                original_name=original_name,
                external_record_id=str(external_record_id).strip(),
                record_type=record_type,
            )
            return favorite
        except (ObjectDoesNotExist, IntegrityError):
            return None

    def get_favorite_by_id(self, favorite_id: int) -> Optional[Favorite]:
        """
        Get favorite by ID.
        """
        try:
            return Favorite.objects.get(id=favorite_id)
        except ObjectDoesNotExist:
            return None

    def get_user_favorites(
        self, user_id: int, record_type: str = None
    ) -> List[Favorite]:
        """
        Get all favorites for a user, optionally filtered by record type.
        """
        queryset = Favorite.objects.filter(user_id=user_id)
        if record_type:
            queryset = queryset.filter(record_type=record_type)
        return list(queryset.order_by("-created_at"))

    def update_favorite_title(
        self, favorite_id: int, custom_title: str
    ) -> Optional[Favorite]:
        """
        Update the custom title of a favorite.
        """
        try:
            favorite = Favorite.objects.get(id=favorite_id)
            favorite.custom_title = custom_title
            favorite.save()
            return favorite
        except ObjectDoesNotExist:
            return None

    def delete_favorite_by_id(self, favorite_id: int) -> bool:
        """
        Delete favorite by ID.
        """
        try:
            favorite = Favorite.objects.get(id=favorite_id)
            favorite.delete()
            return True
        except ObjectDoesNotExist:
            return False

    def delete_user_favorite_by_type(
        self, user_id: int, record_type: str, external_record_id: str = None
    ) -> bool:
        """
        Delete favorite(s) by user ID and record type.
        If external_record_id is provided, delete specific record.
        """
        try:
            queryset = Favorite.objects.filter(user_id=user_id, record_type=record_type)
            if external_record_id:
                queryset = queryset.filter(external_record_id=external_record_id)

            deleted_count = queryset.delete()[0]
            return deleted_count > 0
        except Exception:
            return False

    def favorite_exists(
        self, user_id: int, external_record_id: str, record_type: str
    ) -> bool:
        """
        Check if favorite already exists for user.
        """
        return Favorite.objects.filter(
            user_id=user_id,
            external_record_id=external_record_id,
            record_type=record_type,
        ).exists()

    def get_user_custom_names_mapping(
        self, user_id: int, record_type: str
    ) -> Dict[str, str]:
        favorites = (
            Favorite.objects.filter(user_id=user_id, record_type=record_type)
            .exclude(custom_title__isnull=True)
            .exclude(custom_title__exact="")
        )
        return {
            str(f.external_record_id).strip(): f.custom_title.strip() for f in favorites
        }

    def get_user_favorited_external_ids(self, user_id: int, record_type: str) -> set:
        q = Favorite.objects.filter(
            user_id=user_id, record_type=record_type
        ).values_list("external_record_id", flat=True)
        return {str(eid).strip() for eid in q if eid is not None and str(eid).strip()}

    def search_user_favorites(self, user_id: int, record_type: str, search: str):
        s = (search or "").strip()
        if not s:
            return Favorite.objects.none()
        return (
            Favorite.objects.filter(user_id=user_id, record_type=record_type)
            .filter(custom_title__icontains=s)
            .only("external_record_id", "custom_title")
        )
