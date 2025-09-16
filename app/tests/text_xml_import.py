import os
import xml.etree.ElementTree as ET
from django.test import TestCase
from django.core.management import call_command
from app.models import PointOfInterest
from tempfile import NamedTemporaryFile


class ImportXMLFileDataCommandTests(TestCase):

    def setUp(self) -> None:
        data = [
            {
                "pid": 1, 
                "pname": "ちぬまん", 
                "pcategory": "restaurant",
                "platitude": 43.0479552005377,
                "plongitude": 6.1494078,
                "pratings": "3.0,4.0,3.0,5.0,2.0,3.0,2.0,2.0,2.0,2.0"
            },
            {
                "pid": 2, 
                "pname": "Otter Creek State Forest", 
                "pcategory": "nature-reserve",
                "platitude": 43.0479552005377,
                "plongitude": 6.1494078,
                "pratings": "3.0,4.0,3.0,5.0,2.0,3.0,2.0,2.0,2.0,2.0"
            }
        ]

        # Create XML root
        root = ET.Element("RECORDS")
        for obj in data:
            item_el = ET.SubElement(root, "DATA_RECORD")
            for k, v in obj.items():
                child = ET.SubElement(item_el, k)
                child.text = str(v)

        self.temp_file = NamedTemporaryFile(mode="w+", delete=False, suffix=".xml")
        tree = ET.ElementTree(root)
        tree.write(self.temp_file, encoding="unicode", xml_declaration=True)

        self.temp_file.flush() # ensure data is written to disk
        self.temp_file.seek(0) # Moves the file pointer back to the beginning, to read immediately
        self.temp_file.close()

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def test_xml_file_import(self):
        call_command("import", self.temp_file.name)
        # Assert that objects were created
        self.assertEqual(PointOfInterest.objects.count(), 2)

        poi_1 = PointOfInterest.objects.get(external_id=1)
        self.assertEqual(poi_1.name, "ちぬまん")
        self.assertEqual(poi_1.category, "restaurant")

        poi_2 = PointOfInterest.objects.get(external_id=2)
        self.assertEqual(poi_2.name, "Otter Creek State Forest")
        self.assertEqual(poi_2.category, "nature-reserve")
