import csv
import json
from typing import Iterator
from pathlib import Path

import lxml.etree as etree

from app.file_processor.base import FileProcessor


class CSVFileProcessor(FileProcessor):
    def read_file_content(self, file_path: Path) -> Iterator[dict]:
        with file_path.open("r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            yield from reader

    def row_to_dict(self, row: dict) -> dict:
        ratings = row.get("poi_ratings").strip("{}").split(",")
        ratings_values = [float(item) for item in ratings]
        return {
            "external_id": row.get("poi_id"),
            "name": row.get("poi_name"),
            "latitude": row.get("poi_latitude"),
            "longitude": row.get("poi_longitude"),
            "category": row.get("poi_category"),
            "description": row.get("description", ""),
            "ratings": ratings_values,
            "average_rating": sum(ratings_values) / len(ratings_values)
        }


class JSONFileProcessor(FileProcessor):
    def read_file_content(self, file_path: Path) -> Iterator[dict]:
        with file_path.open("r", encoding="utf-8") as json_file:
            data = json.load(json_file)
            yield from data

    def row_to_dict(self, row: dict) -> dict:
        ratings = row.get("ratings")
        ratings_values = [float(item) for item in ratings]
        return {
            "external_id": row.get("id"),
            "name": row.get("name"),
            "latitude": row.get("coordinates", {}).get("latitude"),
            "longitude": row.get("coordinates", {}).get("longitude"),
            "category": row.get("category"),
            "description": row.get("description"),
            "ratings": ratings_values,
            "average_rating": sum(ratings_values) / len(ratings_values)
        }


class XMLFileProcessor(FileProcessor):
    def read_file_content(self, file_path: Path) -> Iterator[dict]:
        for _, elem in etree.iterparse(file_path, events=["end"], recover=True):
            if elem.tag == "DATA_RECORD":
                row = {
                    child.tag: child.text.strip() if child.text else None
                    for child in elem
                }
                yield row
                elem.clear()

    def row_to_dict(self, row: dict) -> dict:
        ratings = row.get("pratings").split(",")
        ratings_values = [float(item) for item in ratings]
        return {
            "external_id": row.get("pid"),
            "name": row.get("pname"),
            "latitude": row.get("platitude"),
            "longitude": row.get("plongitude"),
            "category": row.get("pcategory"),
            "description": row.get("pdescription", ""),
            "ratings": ratings_values,
            "average_rating": sum(ratings_values) / len(ratings_values)
        }
