import logging
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from starfavs.favorites.data.db_repository import FavoriteRepository
from starfavs.favorites.presentation.serializers import (
    FavoriteCreateSerializer,
    FavoriteUpdateSerializer,
    FavoriteResponseSerializer,
)
from starfavs.favorites.data.content_service import ContentService

from starfavs.favorites.presentation.content_serializers import (
    MovieContentSerializer,
    PlanetContentSerializer,
)

from starfavs.favorites.domain.use_cases.use_cases import (
    CreateFavoriteUC,
    CreateFavoriteInput,
    UpdateFavoriteUC,
    UpdateFavoriteInput,
    DeleteFavoriteByIdUC,
    DeleteFavoriteByIdInput,
    DeleteUserFavoritesByTypeUC,
    DeleteUserFavoritesByTypeInput,
    GetUserFavoritesUC,
    GetUserFavoritesInput,
    DeleteUserFavoriteStrictUC,
    DeleteUserFavoriteStrictInput,
    ListContentWithCustomizationsUC
)

from starfavs.favorites.presentation.types import ContentListResponse,ListContentInput

favorite_repository = FavoriteRepository()

content_service = ContentService()
create_fav_use_case = CreateFavoriteUC(favorite_repository)
update_fav_use_case = UpdateFavoriteUC(favorite_repository)
delete_fav_use_case = DeleteFavoriteByIdUC(favorite_repository)
delete_by_type_use_case = DeleteUserFavoritesByTypeUC(favorite_repository)
get_user_favs_use_case = GetUserFavoritesUC(favorite_repository)
delete_strict_use_case = DeleteUserFavoriteStrictUC(favorite_repository)
list_content_use_case = ListContentWithCustomizationsUC(content_service)


@api_view(["POST"])
def create_favorite(request):
    serializer = FavoriteCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        fav = create_fav_use_case.execute(
            CreateFavoriteInput(**serializer.validated_data)
        )
        return Response(
            FavoriteResponseSerializer(fav).data, status=status.HTTP_201_CREATED
        )
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
def update_favorite(request, favorite_id):
    serializer = FavoriteUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        fav = update_fav_use_case.execute(
            UpdateFavoriteInput(
                favorite_id=favorite_id,
                custom_title=serializer.validated_data["custom_title"],
            )
        )
        return Response(FavoriteResponseSerializer(fav).data, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


@api_view(["DELETE"])
def delete_favorite(request, favorite_id):
    ok = delete_fav_use_case.execute(DeleteFavoriteByIdInput(favorite_id=favorite_id))
    return Response(
        status=status.HTTP_204_NO_CONTENT if ok else status.HTTP_404_NOT_FOUND
    )


@api_view(["DELETE"])
def delete_user_favorites_by_type(request, user_id, record_type):
    external_record_id = request.query_params.get("external_record_id")
    ok = delete_by_type_use_case.execute(
        DeleteUserFavoritesByTypeInput(
            user_id=user_id,
            record_type=record_type,
            external_record_id=external_record_id,
        )
    )
    return Response(
        status=status.HTTP_204_NO_CONTENT if ok else status.HTTP_404_NOT_FOUND
    )


@api_view(["GET"])
def get_user_favorites(request, user_id):
    record_type = request.query_params.get("record_type")
    favs = get_user_favs_use_case.execute(
        GetUserFavoritesInput(user_id=user_id, record_type=record_type)
    )
    return Response(
        FavoriteResponseSerializer(favs, many=True).data, status=status.HTTP_200_OK
    )


@api_view(["DELETE"])
def delete_user_favorite_by_id(request, user_id, record_type, favorite_id):
    try:
        ok = delete_strict_use_case.execute(
            DeleteUserFavoriteStrictInput(
                user_id=user_id, record_type=record_type, favorite_id=favorite_id
            )
        )
        return Response(
            status=status.HTTP_204_NO_CONTENT if ok else status.HTTP_400_BAD_REQUEST
        )
    except PermissionError as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
def list_content_with_customizations(request,record_type):
    """List content for a given record type for a user"""

    # Fetch parameters from the request
    user_id = request.query_params.get("user_id")
    page = int(request.query_params.get("page", 1))
    limit = int(request.query_params.get("limit", 10))
    search = request.query_params.get("search")

    if not user_id:
        return Response(
            {"error": "user_id parameter is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        user_id = int(user_id)
    except ValueError:
        return Response(
            {"error": "user_id must be a valid integer"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    # Validate record type
    if record_type not in ["movie", "planet"]:
        return Response(
            {"error": 'record_type must be either "movie" or "planet"'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    # Execute the use case to get the content items
    content_items: ContentListResponse = list_content_use_case.execute(
        ListContentInput(
            user_id=user_id,
            record_type=record_type,
            page=page,
            limit=limit,
            search=search,
        )
    )

    # Serialize the content items to return only the fields we need
    if record_type == "movie":
        serialized_favorite_items = MovieContentSerializer(content_items.results, many=True)
    else:
        serialized_favorite_items = PlanetContentSerializer(content_items.results, many=True)

    return Response(
        {
            "count": content_items.count,
            "next": content_items.next,
            "previous": content_items.previous,
            "results": serialized_favorite_items.data,
            "total_favorites": content_items.total_favorites,
            "request_info": {
                "user_id": user_id,
                "record_type": record_type,
                "page": page,
                "limit": limit,
                "search": search or "",
            },
        },
        status=status.HTTP_200_OK,
    )


