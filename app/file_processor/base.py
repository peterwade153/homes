from abc import ABC, abstractclassmethod
from typing import Iterator
from pathlib import Path


class FileProcessor(ABC):
    @abstractclassmethod
    def read_file_content(self, file_path: Path) -> Iterator[dict]:
        pass

    @abstractclassmethod
    def row_to_dict(self, row: dict) -> dict:
        pass
