import csv
import hashlib
import json
import time
from enum import Enum
from typing import Any
from typing import Optional
from typing import List
from typing import Iterator
from pathlib import Path

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.core.management.base import CommandParser
import lxml.etree as etree

from app.models import PointOfInterest
from app.models import FileHash


class FileFormatEnum(Enum):
    CSV = ".csv"
    JSON = ".json"
    XML = ".xml"


class Command(BaseCommand):
    help = "Import Point of Interest data from CSV, JSON, XML files"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "paths",
            nargs="+",
            type=str,
            help="Path(s) to CSV, JSON, XML file(s) or directory(ies)",
        )
    
    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        chunk_size = 8192
        paths = options["paths"]

        start_time = time.perf_counter()

        file_paths = self._get_file_paths(paths=paths)
        if not file_paths:
            raise CommandError("No file paths found")

        for file_path in file_paths:
            file_hash = self._get_file_hash(file_path=file_path, chunk_size=chunk_size)
            existing_file_hash = FileHash.objects.filter(file_hash=file_hash).exists()
            if existing_file_hash:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping '{file_path}': File already imported."
                    )
                )
                continue

            self._process_file(
                file_path=file_path, file_hash=file_hash, batch_size=chunk_size
            )

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        print("+++++++++++++++++++++")
        print(f"Import execution time: {elapsed_time:.6f} seconds")
        print("+++++++++++++++++++++---")

    @staticmethod
    def _get_file_paths(paths: List[str]) -> List[Path]:
        """
        Finds file(s) path(s), with the supported File Formats
        Returns:
            A list of Path objects for all found data files.
        """
        file_paths = []
        supported_formats = {fmt.value for fmt in FileFormatEnum}

        for p in paths:
            path = Path(p)
            if path.is_file() and path.suffix.lower() in supported_formats:
                file_paths.append(path)
            elif path.is_dir():
                file_paths.extend(
                    [
                        file
                        for file in path.iterdir()
                        if file.is_file() and file.suffix.lower() in supported_formats
                    ]
                )
            else:
                raise CommandError(
                    f"Invalid Path, or Unsupported file format {p} "
                    f"Supported formats {', '.join(supported_formats)}"
                )
        return file_paths

    @staticmethod
    def _get_file_hash(file_path: Path, chunk_size: int) -> str:
        """
        Generates a SHA-256 hash for a file, reading it in chunks.
        """
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def _get_rows_from_file(file_path: Path) -> Iterator[dict]:
        """
        Reads a file and yields POI data
        """
        suffix = file_path.suffix.lower()

        if suffix == FileFormatEnum.CSV.value:
            with file_path.open("r", encoding="utf-8") as csv_file:
                reader = csv.DictReader(csv_file)
                yield from reader
        elif suffix == FileFormatEnum.JSON.value:
            with file_path.open("r", encoding="utf-8") as json_file:
                data = json.load(json_file)
                if isinstance(data, dict):
                    yield data
                else:
                    yield from data
        elif suffix == FileFormatEnum.XML.value:
            for _, elem in etree.iterparse(file_path, events=["end"], recover=True):
                if elem.tag == "DATA_RECORD":
                    row = {
                        child.tag: child.text.strip() if child.text else None
                        for child in elem
                    }
                    yield row
                    elem.clear()
    
    def _process_file(self, file_path: Path, batch_size: int, file_hash: str) -> None:
        """
        Processes a file in batches and inserts records in the database table
        """
        batch = []
        total_imported = 0

        try:
            row_iter = self._get_rows_from_file(file_path=file_path)
            for row in row_iter:
                batch.append(self._row_to_poi(row=row))
                if len(batch) >= batch_size:
                    self._bulk_insert(batch=batch)
                    total_imported += len(batch)
                    batch.clear()

            # Insert any remaining records in the last batch
            if batch:
                self._bulk_insert(batch)
                total_imported += len(batch)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully imported {total_imported} Point of Interest records from {file_path}"
                )
            )
            if total_imported > 0:
                # Add hash for imported file
                FileHash.objects.create(file_hash=file_hash)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error processing {file_path}: {e}"))

    @staticmethod
    def _row_to_poi(row: dict) -> PointOfInterest:
        """
        Transforms row dictionary into PointOfInterest model instance,
        """
        external_id = row.get("poi_id") or row.get("id") or row.get("pid")
        name = row.get("poi_name") or row.get("name") or row.get("pname")
        latitude = (
            row.get("poi_latitude")
            or row.get("coordinates", {}).get("latitude")
            or row.get("platitude")
        )
        longitude = (
            row.get("poi_longitude")
            or row.get("coordinates", {}).get("longitude")
            or row.get("plongitude")
        )
        category = (
            row.get("poi_category") or row.get("category") or row.get("pcategory")
        )
        description = row.get("description", "")

        ratings = []
        if "poi_ratings" in row:
            ratings = row.get("poi_ratings").strip("{}").split(",")
        elif "ratings" in row:
            ratings = row.get("ratings")
        elif "pratings" in row:
            ratings = row.get("pratings").split(",")

        ratings_values = [float(item) for item in ratings]
        average_rating = sum(ratings_values) / len(ratings_values)

        return PointOfInterest(
            external_id=external_id.strip(),
            name=str(name),
            description=description.strip(),
            category=category.strip(),
            point=Point(float(longitude), float(latitude)),
            average_rating=average_rating,
            ratings=ratings_values,
        )

    @staticmethod
    def _bulk_insert(batch: List[PointOfInterest]) -> None:
        PointOfInterest.objects.bulk_create(batch, ignore_conflicts=True)
