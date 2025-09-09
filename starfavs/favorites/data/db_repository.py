from typing import Optional, List, Dict
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from starfavs.favorites.domain.models import Favorite
from starfavs.user.domain.models import User


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

    def delete_favorites(
        self,
        favorite_id: int = None,
        user_id: int = None,
        record_type: str = None,
        external_record_id: str = None,
    ) -> bool:
        """
        Priority 1: favorite_id (highest) - Delete specific favorite by ID
        Priority 2: external_record_id - Delete specific item for user/type
        Priority 3: user_id + record_type - Bulk delete all items for user/type
        """
        try:
            if favorite_id:
                # Scenario 1: Delete by favorite ID
                favorite = Favorite.objects.get(id=favorite_id)
                favorite.delete()
                return True

            elif user_id and record_type:
                # Scenario 2 & 3: Delete by user criteria
                queryset = Favorite.objects.filter(
                    user_id=user_id, record_type=record_type
                )
                if external_record_id:
                    queryset = queryset.filter(external_record_id=external_record_id)

                deleted_count = queryset.delete()[0]
                return deleted_count > 0

            else:
                return False

        except ObjectDoesNotExist:
            return False
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

    def get_user_favorites(
        self,
        user_id: int,
        record_type: str | None = None,
    ) -> List[Favorite]:
        favorites = Favorite.objects.filter(user_id=user_id)

        if record_type:
            favorites = favorites.filter(record_type=record_type)

        return list(favorites.order_by("-created_at"))
