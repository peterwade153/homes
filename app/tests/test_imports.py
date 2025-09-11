import os
from django.test import TestCase
from django.core.management import call_command
from app.models import PointOfInterest
from tempfile import NamedTemporaryFile


class ImportFileDataCommandTests(TestCase):

    def test_csv_file_import(self):
        csv_file_content = """poi_id,poi_name,poi_category,poi_latitude,poi_longitude,poi_ratings
    1,ちぬまん,restaurant,26.2155192001422,127.6854314,{3.0,4.0,3.0,5.0,2.0,3.0,2.0,2.0,2.0,2.0}
    2,Otter Creek State Forest,nature-reserve,43.7149419232782,-75.3263056920684,{3.0,4.0,3.0,5.0,2.0,3.0,2.0,2.0,2.0,2.0}
    """
        tmp_file_path = ""
        with NamedTemporaryFile(mode="w+", delete=False, suffix=".csv") as tmp_file:
            tmp_file.write(csv_file_content)
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
