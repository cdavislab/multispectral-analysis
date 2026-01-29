
from dataclasses import dataclass
from typing import Optional
import os

@dataclass
class ImageMeta:
    """Metadata for a single image."""
    key: str
    group: int
    kind: str           # "input" or "processed"
    keyword: Optional[str] = None
    nickname: Optional[str] = None
    statistics: Optional[dict] = None

class MetadataStore:
    def __init__(self):
        self.items: list[ImageMeta] = []

    @property
    def keys(self):
        return [m.key for m in self.items]
    
    @property
    def basenames(self):
        return [os.path.splitext(os.path.basename(m.key))[0] for m in self.items]

    @property
    def nicknames(self):
        return [m.nickname for m in self.items]

    def add(self, meta: ImageMeta):
        self.items.append(meta)

    def delete(self, key: str):
        self.items = [m for m in self.items if m.key != key]

    def by_group(self, group: int):
        return [m for m in self.items if m.group == group]

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
    
    def change_group(self, key: str, new_group: int):
        """
        Changes the group of an image metadata entry.
        """
        for meta in self.items:
            if meta.key == key:
                meta.group = new_group