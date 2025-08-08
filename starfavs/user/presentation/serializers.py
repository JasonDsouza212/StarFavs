from rest_framework import serializers
from starfavs.user.domain.models import User


class UserCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a new user.
    """

    email = serializers.EmailField()
    name = serializers.CharField(max_length=100)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "name"]
