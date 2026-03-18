
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
    import_order: Optional[int] = None  # Stable insertion order token

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
        self._next_import_order = 1

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
        groups = []
        seen = set()
        for meta in self.items:
            if visible_only and not meta.visible:
                continue
            if meta.group in seen:
                continue
            seen.add(meta.group)
            groups.append(meta.group)
        return groups

    def nicknames(self, visible_only=False):
        if visible_only:
            return [m.nickname for m in self.items if m.visible]
        return [m.nickname for m in self.items]

    def add(self, meta: ImageMeta):
        for i, m in enumerate(self.items):
            if m.nickname == meta.nickname:
                if meta.import_order is None:
                    meta.import_order = m.import_order
                self.items[i] = meta
                return
        if meta.import_order is None:
            meta.import_order = self._next_import_order
            self._next_import_order += 1
        self.items.append(meta)

    def visible_indices(self) -> list[int]:
        return [i for i, meta in enumerate(self.items) if meta.visible]

    def move_item(self, from_idx: int, to_idx: int) -> None:
        if from_idx == to_idx:
            return
        item = self.items.pop(from_idx)
        self.items.insert(to_idx, item)

    def move_items(self, from_indices: list[int], to_index: int) -> bool:
        """Move a block of items to *to_index* while preserving relative order.

        Parameters
        ----------
        from_indices:
            Absolute indices in ``self.items`` to move as one block.
        to_index:
            Absolute destination index in the pre-move list.

        Returns
        -------
        bool
            True when list order changed, otherwise False.
        """
        if len(from_indices) == 0:
            return False

        unique_sorted = sorted(set(from_indices))
        if any(i < 0 or i >= len(self.items) for i in unique_sorted):
            return False
        if to_index < 0 or to_index > len(self.items):
            return False
        if to_index >= unique_sorted[0] and to_index <= (unique_sorted[-1] + 1):
            return False

        move_set = set(unique_sorted)
        block = [self.items[i] for i in unique_sorted]
        remaining = [item for i, item in enumerate(self.items) if i not in move_set]

        removed_before_target = sum(1 for i in unique_sorted if i < to_index)
        insert_at = to_index - removed_before_target
        if insert_at < 0:
            insert_at = 0
        if insert_at > len(remaining):
            insert_at = len(remaining)

        self.items = remaining[:insert_at] + block + remaining[insert_at:]
        return True

    def sort_items(self, sort_key: str, reverse: bool = False) -> None:
        def text_key(value) -> str:
            if value is None:
                return ""
            return str(value).casefold()

        def group_rank(value) -> tuple[int, str]:
            if value == "default":
                return (1, "")
            try:
                return (0, f"{int(value):010d}")
            except (TypeError, ValueError):
                return (0, text_key(value))

        def key_func(meta: ImageMeta):
            nickname = meta.nickname or ""
            basename = os.path.basename(nickname)
            parent = os.path.basename(os.path.dirname(nickname))

            if sort_key == "basename":
                return (text_key(basename), text_key(parent), text_key(meta.key))
            if sort_key == "parent_path":
                return (text_key(parent), text_key(basename), text_key(meta.key))
            if sort_key == "group":
                return (group_rank(meta.group), text_key(meta.keyword), text_key(basename), text_key(meta.key))
            if sort_key == "keyword":
                return (text_key(meta.keyword), group_rank(meta.group), text_key(basename), text_key(meta.key))
            return (
                meta.import_order if meta.import_order is not None else 10**9,
                text_key(meta.key),
            )

        self.items.sort(key=key_func, reverse=reverse)

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