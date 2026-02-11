
from dataclasses import dataclass
from typing import Optional
import os

@dataclass
class ImageMeta:
    """Metadata for a single image."""
    key: str                        # Unique identifier for the image
    group: str                      # Group identifier for the image
    kind: str                       # "input" or "processed"
    visible: bool = True            # Whether the image is visible in the UI
    keyword: Optional[str] = None   # Keyword shared amongst files
    common_name: Optional[str] = None   # Common name for grouping in the UI
    nickname: Optional[str] = ''  # User-defined nickname for the UI
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
        return [os.path.splitext(os.path.basename(m.nickname))[0] for m in self.items]

    def groups(self, visible_only=False):
        if visible_only:
            return list(set(m.group for m in self.items if m.visible))
        return list(set(m.group for m in self.items))

    def nicknames(self, visible_only=False):
        if visible_only:
            return [m.nickname for m in self.items if m.visible]
        return [m.nickname for m in self.items]

    def add(self, meta: ImageMeta):
        self.items.append(meta)

    def delete(self, key: str):
        self.items = [m for m in self.items if m.key != key]

    def by_group(self, group: int | str):
        return [m for m in self.items if m.group == group]
    
    def by_basename(self, basename: str):
        return [m for m in self.items if os.path.splitext(os.path.basename(m.nickname))[0] == basename]

    def new_key(self):
        existing_keys = {m.key for m in self.items}
        # If existing_keys is empty, start from 1
        i = 1
        while str(i) in existing_keys:
            i += 1
        return str(i)
    
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
            groups.add(self.items[i].group)

        return list(groups)