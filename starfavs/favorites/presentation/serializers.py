from rest_framework import serializers
from starfavs.favorites.domain.models import Favorite, RecordType


class FavoriteCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    custom_title = serializers.CharField(
        max_length=200, required=False, allow_blank=True, allow_null=True
    )
    original_name = serializers.CharField(max_length=200)
    external_record_id = serializers.CharField(max_length=50)
    record_type = serializers.ChoiceField(choices=RecordType.choices)


class FavoriteUpdateSerializer(serializers.Serializer):
    custom_title = serializers.CharField(
        max_length=200, required=False, allow_blank=True, allow_null=True
    )


class FavoriteResponseSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.name", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Favorite
        fields = [
            "id",
            "user_id",
            "user_name",
            "user_email",
            "custom_title",
            "original_name",
            "external_record_id",
            "record_type",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "user_name",
            "user_email",
            "external_record_id",
            "record_type",
            "original_name",
        ]
