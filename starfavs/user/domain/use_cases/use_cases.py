# starfavs/user/domain/use_cases.py
from dataclasses import dataclass
from typing import Optional, List
from starfavs.user.data.db_repository import UserRepository
from starfavs.user.domain.models import User
from starfavs.user.presentation.types import CreateUserInput


class CreateUserUseCase:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def execute(self, input: CreateUserInput) -> User:
        return self.repo.create_user(email=input.email, name=input.name)


class DeleteUserUseCase:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def execute(self, user_id: int) -> bool:
        return self.repo.delete_user(user_id)


class GetUserUseCase:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def execute(self, user_id: int) -> Optional[User]:
        return self.repo.get_user_by_id(user_id)


class ListUsersUseCase:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def execute(self) -> List[User]:
        return self.repo.get_all_users()
