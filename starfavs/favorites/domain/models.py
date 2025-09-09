from django.db import models
from starfavs.user.domain.models import User


class RecordType(models.TextChoices):
    MOVIE = "movie", "Movie"
    PLANET = "planet", "Planet"


class Favorite(models.Model):
    """
    Model to store user favorites for movies and planets.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    # TODO: Add indexing for faster searching
    custom_title = models.CharField(
        max_length=200, blank=True, null=True
    )  
    original_name = models.CharField(max_length=200)
    external_record_id = models.CharField(max_length=50)  # ID from external API
    record_type = models.CharField(max_length=10, choices=RecordType.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "starfavs_favorites"
        unique_together = ["user", "external_record_id", "record_type"]

    def __str__(self):
        return f"{self.user.name}'s {self.record_type}: {self.custom_title}"
