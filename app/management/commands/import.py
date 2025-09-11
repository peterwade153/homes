import hashlib
import time
from typing import Any
from typing import Optional
from typing import List
from pathlib import Path

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.core.management.base import CommandParser

from app.models import FileHash
from app.models import PointOfInterest
from app.file_processor.file_formats import FileFormatEnum
from app.file_processor.processors import CSVFileProcessor
from app.file_processor.processors import JSONFileProcessor
from app.file_processor.processors import XMLFileProcessor


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
        file_processor_map = {
            FileFormatEnum.CSV.value : CSVFileProcessor(),
            FileFormatEnum.JSON.value: JSONFileProcessor(),
            FileFormatEnum.XML.value: XMLFileProcessor()
        }

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
                file_path=file_path,
                file_hash=file_hash, 
                batch_size=chunk_size,
                file_processor_map = file_processor_map
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
            if path.is_file():
                if path.suffix.lower() in supported_formats:
                    file_paths.append(path)
                else:
                    raise CommandError(
                        f"Unsupported file format {p}"
                        f" Supported formats {', '.join(supported_formats)}"
                    )
            elif path.is_dir():
                file_paths.extend(
                    [
                        file
                        for file in path.iterdir()
                        if file.is_file() and file.suffix.lower() in supported_formats
                    ]
                )
            else:
                raise CommandError(f"Invalid Path {p} ")
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
    
    def _process_file(self, file_path: Path, batch_size: int, file_hash: str, file_processor_map: dict) -> None:
        """
        Processes a file in batches and inserts records in the database table
        """
        batch = []
        total_imported = 0

        try:
            processor_key = file_path.suffix.lower()
            file_processor = file_processor_map.get(processor_key)
            row_iter = file_processor.read_file_content(file_path=file_path)
            for row in row_iter:
                print('----')
                print(row)
                row_dict = file_processor.row_to_dict(row=row)
                poi = PointOfInterest(
                    external_id=row_dict.get("external_id"),
                    name=row_dict.get("name"),
                    description=row_dict.get("description", ""),
                    category=row_dict.get("category"),
                    point=Point(float(row_dict.get("latitude")), float(row_dict.get("longitude"))),
                    average_rating=row_dict.get("average_rating"),
                    ratings=row_dict.get("ratings"),
                )
                batch.append(poi)
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
    def _bulk_insert(batch: List[PointOfInterest]) -> None:
        PointOfInterest.objects.bulk_create(batch, ignore_conflicts=True)
