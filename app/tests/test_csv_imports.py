import io
import os
import csv
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from app.models import PointOfInterest
from tempfile import NamedTemporaryFile


class ImportFileDataCommandTests(TestCase):

    def setUp(self) -> None:
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
        self.temp_file = NamedTemporaryFile(mode="w+", delete=False, suffix=".csv")
        writer = csv.DictWriter(self.temp_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        self.temp_file.flush()
        self.temp_file.close()

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def test_csv_file_import(self):
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

    def test_invalid_import_output(self):
        with self.assertRaisesMessage(CommandError, "Invalid Path sample"):
            call_command("import", "sample")

    def test_unsupported_file_format_import_output(self):
        with self.assertRaisesMessage(CommandError, "Invalid Path sample.txt"):
            call_command("import", "sample.txt")

    def test_no_paths_found_output(self):
        with self.assertRaisesMessage(CommandError, "No file paths found"):
            call_command("import", "")
    