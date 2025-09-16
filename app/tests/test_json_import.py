import io
import json
import os
from django.test import TestCase
from django.core.management import call_command
from app.models import PointOfInterest
from tempfile import NamedTemporaryFile


class ImportJsonFileDataCommandTests(TestCase):

    def setUp(self) -> None:
        data = [
            {
                "id": 1, 
                "name": "ちぬまん", 
                "category": "restaurant",
                "description": "poytpahip",
                "coordinates": {
                    "latitude": 43.0479552005377,
                    "longitude": 6.1494078
                },
                "ratings": [3.0,4.0,3.0,5.0,2.0,3.0,2.0,2.0,2.0,2.0]
            },
            {
                "id": 2, 
                "name": "Otter Creek State Forest", 
                "category": "nature-reserve",
                "description": "heqdetbl",
                "coordinates": {
                    "latitude": 43.0479552005377,
                    "longitude": 6.1494078
                }, 
                "ratings": [3.0,4.0,3.0,5.0,2.0,3.0,2.0,2.0,2.0,2.0]
            }
        ]
        self.temp_file = NamedTemporaryFile(mode="w+", delete=False, suffix=".json")
        json.dump(data, self.temp_file, indent=2)
        self.temp_file.flush() # ensure data is written to disk
        self.temp_file.seek(0) # Moves the file pointer back to the beginning, to read immediately
        self.temp_file.close()

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def test_json_file_import(self):
        call_command("import", self.temp_file.name)
        # Assert that objects were created
        self.assertEqual(PointOfInterest.objects.count(), 2)

        poi_1 = PointOfInterest.objects.get(external_id=1)
        self.assertEqual(poi_1.name, "ちぬまん")
        self.assertEqual(poi_1.category, "restaurant")

        poi_2 = PointOfInterest.objects.get(external_id=2)
        self.assertEqual(poi_2.name, "Otter Creek State Forest")
        self.assertEqual(poi_2.category, "nature-reserve")

    def test_command_output(self):
        # Capture stdout
        out = io.StringIO()
        call_command("import", self.temp_file.name, stdout=out)
        self.assertIn(
            f"Successfully imported 2 Point of Interest records from {self.temp_file.name}", 
            out.getvalue()
        )
