import os
import csv
from django.test import TestCase
from django.core.management import call_command
from app.models import PointOfInterest
from tempfile import NamedTemporaryFile


class ImportFileDataCommandTests(TestCase):

    def test_csv_file_import(self):
        data = [
            {
                "poi_id": 1, 
                "poi_name": "ちぬまん", 
                "poi_category": "restaurant", 
                "poi_latitude": "26.2155192001422", 
                "poi_longitude": "127.6854314", 
                "poi_ratings": "{3.0,4.0,3.0,5.0,2.0,3.0,2.0,2.0,2.0,2.0}"
            },
            {
                "poi_id": 2, 
                "poi_name": "Otter Creek State Forest", 
                "poi_category": "nature-reserve", 
                "poi_latitude": "43.7149419232782", 
                "poi_longitude": "-75.3263056920684", 
                "poi_ratings": "{3.0,4.0,3.0,5.0,2.0,3.0,2.0,2.0,2.0,2.0}"
            }
        ]
        fieldnames = ["poi_id", "poi_name", "poi_category", "poi_latitude", "poi_longitude", "poi_ratings"]
        tmp_file_path = ""
        with NamedTemporaryFile(mode="w+", delete=False, suffix=".csv") as tmp_file:
            writer = csv.DictWriter(tmp_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

            # tmp_file.write(csv_file_content)
            tmp_file_path = tmp_file.name

        try:
            # Call the management command
            call_command("import", tmp_file_path)
            # Assert that objects were created
            self.assertEqual(PointOfInterest.objects.count(), 2)

            poi_1 = PointOfInterest.objects.get(external_id=1)
            self.assertEqual(poi_1.name, "ちぬまん")
            self.assertEqual(poi_1.category, "restaurant")

            poi_2 = PointOfInterest.objects.get(external_id=2)
            self.assertEqual(poi_2.name, "Otter Creek State Forest")
            self.assertEqual(poi_2.category, "nature-reserve")
        finally:
            # Clean up temporary file
            os.remove(tmp_file_path)
