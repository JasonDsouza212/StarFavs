from typing import Optional, List
from django.core.exceptions import ObjectDoesNotExist
from starfavs.user.domain.models import User


class UserRepository:

    def create_user(self, email: str, name: str) -> User:
        user = User.objects.create(email=email, name=name)
        return user

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        """
        try:
            return User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            return None

    def get_all_users(self) -> List[User]:
        """
        Get all users.
        """
        return list(User.objects.all())

    def delete_user(self, user_id: int) -> bool:
        """
        Delete user by ID.
        """
        try:
            user = User.objects.get(id=user_id)
            user.delete()
            return True
        except ObjectDoesNotExist:
            return False
