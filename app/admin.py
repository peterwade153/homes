from django.contrib import admin

from app.models import PointOfInterest

@admin.register(PointOfInterest)
class PointOfInterestAdmin(admin.ModelAdmin):
    list_display = ["id", "external_id", "name", "category", "average_rating", "point"]
    list_filter = ["category"]
    search_fields = ["=id", "=external_id"]
