from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from starfavs.user.data.db_repository import UserRepository
from starfavs.user.presentation.serializers import UserCreateSerializer, UserSerializer

from starfavs.user.domain.use_cases.use_cases import (
    CreateUserUseCase,
    CreateUserInput,
    DeleteUserUseCase,
    GetUserUseCase,
    ListUsersUseCase,
)

repo = UserRepository()


@api_view(["POST"])
def create_user(request):
    serializer = UserCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = CreateUserUseCase(repo).execute(
        CreateUserInput(
            email=serializer.validated_data["email"],
            name=serializer.validated_data["name"],
        )
    )
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
def delete_user(request, user_id):
    if not GetUserUseCase(repo).execute(user_id):
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    ok = DeleteUserUseCase(repo).execute(user_id)
    return Response(
        status=status.HTTP_204_NO_CONTENT if ok else status.HTTP_400_BAD_REQUEST
    )


@api_view(["GET"])
def get_user(request, user_id):
    user = GetUserUseCase(repo).execute(user_id)
    if not user:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


@api_view(["GET"])
def list_users(request):
    users = ListUsersUseCase(repo).execute()
    return Response(UserSerializer(users, many=True).data, status=status.HTTP_200_OK)
