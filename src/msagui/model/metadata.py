
from dataclasses import dataclass
from typing import Optional
import csv
import os


def _folder_basename(nickname: str) -> str:
    """Return ``'parent_folder/stem'`` for a file path.

    Using the immediate parent folder plus the stem (filename without extension)
    as the grouping key ensures that files with identical names in different
    folders are placed in separate groups.

    Example::

        /data/condition_A/sample_488.csv  →  "condition_A/sample_488"
        /data/condition_B/sample_488.csv  →  "condition_B/sample_488"
    """
    stem   = os.path.splitext(os.path.basename(nickname))[0]
    parent = os.path.basename(os.path.dirname(nickname))
    return f"{parent}/{stem}" if parent else stem

@dataclass
class ImageMeta:
    """Metadata for a single image."""
    key: str                        # Unique identifier for the image
    group: int | str                      # Group identifier for the image
    kind: str                       # "input" or "processed"
    nickname: str                   # User-defined nickname for the UI
    visible: bool = True            # Whether the image is visible in the UI
    keyword: Optional[str] = None   # Keyword shared amongst files
    common_name: Optional[list[str]] = None  # Common name for grouping in the UI

    statistics: Optional[dict] = None # Dictionary to hold computed statistics for the image
    
    @property
    def hdf5_path(self) -> str:
        """Returns the HDF5 dataset path for this image."""
        if self.group == "default":
            return f"{self.group}/{self.key}"
        return f"/{self.group}/{self.keyword}"

class MetadataStore:
    def __init__(self):
        self.items: list[ImageMeta] = []

    @property
    def keys(self):
        return [m.key for m in self.items]
    
    @keys.setter
    def keys(self, new_keys: list[str]):
        for meta, new_key in zip(self.items, new_keys):
            meta.key = new_key

    @property
    def basenames(self):
        return [_folder_basename(m.nickname) for m in self.items]

    def groups(self, visible_only=False):
        if visible_only:
            return list(set(m.group for m in self.items if m.visible))
        return list(set(m.group for m in self.items))

    def nicknames(self, visible_only=False):
        if visible_only:
            return [m.nickname for m in self.items if m.visible]
        return [m.nickname for m in self.items]

    def add(self, meta: ImageMeta):
        for i, m in enumerate(self.items):
            if m.nickname == meta.nickname:
                self.items[i] = meta
                return
        self.items.append(meta)

    def delete(self, key: str):
        self.items = [m for m in self.items if m.key != key]

    def by_group(self, group: int | str):
        return [m for m in self.items if m.group == group]
    
    def by_basename(self, basename: str):
        return [m for m in self.items if _folder_basename(m.nickname) == basename]

    def new_key(self):
        existing_keys = {m.key for m in self.items}
        # If existing_keys is empty, start from 1
        i = 1
        while str(i) in existing_keys:
            i += 1
        return str(i)

    def export_filelist(self, file_path: str) -> None:
        """Write the file paths of all input images to a CSV with a 'fpath' column."""
        input_items = [item for item in self.items if item.kind == "input"]
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["fpath"])
            for item in input_items:
                writer.writerow([item.nickname])
    
    def change_keyword(self, key: str, new_keyword: str):
        """
        Changes the keyword of an image metadata entry.
        """
        for meta in self.items:
            if meta.key == key:
                meta.keyword = new_keyword
    
    def change_group(self, key: str, new_group: str):
        """
        Changes the group of an image metadata entry.
        """
        for meta in self.items:
            if meta.key == key:
                meta.group = new_group

    def get_group(self, index: int | list[int]) -> list[str]:
        if isinstance(index, int):
            index = [index]

        groups = set()
        for i in index:
            assert i < len(self.items), f"Index {i} out of range for metadata items of length {len(self.items)}"
            groups.add(self.items[i].group)

        return list(groups)