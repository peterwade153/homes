from django.contrib.gis.db.models import PointField
from django.contrib.postgres.fields import ArrayField
from django.db import models


class PointOfInterest(models.Model):
    external_id = models.CharField(max_length=255, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=255, db_index=True)
    point = PointField()
    average_rating = models.FloatField()
    ratings = ArrayField(models.FloatField(), blank=True, default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class FileHash(models.Model):
    file_hash = models.CharField(max_length=64, db_index=True, unique=True)
    created_date = models.DateTimeField(auto_now_add=True)
