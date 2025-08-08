from rest_framework import serializers


class MovieContentSerializer(serializers.Serializer):
    title = serializers.CharField()
    release_date = serializers.CharField()
    created = serializers.CharField()
    edited = serializers.CharField()
    url = serializers.CharField()
    is_favourite = serializers.BooleanField(required=False, default=False)


class PlanetContentSerializer(serializers.Serializer):
    name = serializers.CharField()
    created = serializers.CharField()
    edited = serializers.CharField()
    url = serializers.CharField()
    is_favourite = serializers.BooleanField()
