from types import SimpleNamespace
from typing import Any, cast

import tkinter as tk

from msagui.controller.listbox_controller import FileListController
from msagui.model.metadata import ImageMeta, MetadataStore


class DummyVar:
    def __init__(self, value: Any) -> None:
        self._value = value

    def get(self) -> Any:
        return self._value


class DummyTkListbox:
    def __init__(self) -> None:
        self.items: list[str] = []
        self._selection: set[int] = set()
        self._active = 0

    def nearest(self, y: Any) -> int:
        if not self.items:
            return 0
        return max(0, min(int(y), len(self.items) - 1))

    def curselection(self) -> tuple[int, ...]:
        return tuple(sorted(self._selection))

    def selection_includes(self, idx: Any) -> bool:
        return idx in self._selection

    def selection_clear(self, start: Any, end: Any = None) -> None:
        if start == 0 and end == tk.END:
            self._selection.clear()
            return
        self._selection.discard(int(start))

    def selection_set(self, start: Any, end: Any = None) -> None:
        if end is None:
            self._selection.add(int(start))
            return
        if end == tk.END:
            end_idx = len(self.items) - 1
        else:
            end_idx = int(end)
        for i in range(int(start), end_idx + 1):
            self._selection.add(i)

    def size(self) -> int:
        return len(self.items)

    def itemconfig(self, idx: Any, cfg: Any) -> None:
        return

    def activate(self, idx: Any) -> None:
        self._active = int(idx)

    def get(self, idx: Any) -> str:
        return self.items[int(idx)]

    def bbox(self, idx: Any) -> tuple[int, int, int, int] | None:
        i = int(idx)
        if i < 0 or i >= len(self.items):
            return None
        # x, y, width, height
        return (0, i * 10, 100, 10)


class DummyListboxView:
    def __init__(self) -> None:
        self.file_list = DummyTkListbox()

    def update(self, files: list[str]) -> None:
        self.file_list.items = list(files)
        self.file_list._selection = {i for i in self.file_list._selection if i < len(files)}

    def get_selected_indices(self) -> list[int]:
        return list(self.file_list.curselection())


class DummyModel:
    def __init__(self) -> None:
        self.metadata = MetadataStore()


def test_drag_selected_block_moves_together() -> None:
    """Verify dragging within a multi-selection moves the selected block as a unit."""
    model = DummyModel()
    for key in ["1", "2", "3", "4", "5"]:
        model.metadata.add(
            ImageMeta(key=key, group="A", kind="input", nickname=f"/tmp/{key}.csv")
        )

    listbox_view = DummyListboxView()
    controller = FileListController(
        model=model,
        listbox=cast(Any, listbox_view),
        view_mode=cast(Any, DummyVar("full")),
        show_groups=cast(Any, DummyVar(False)),
        sort_key=cast(Any, DummyVar("time_imported")),
        sort_desc=cast(Any, DummyVar(False)),
    )

    controller.update_listbox()
    listbox_view.file_list.selection_set(1)
    listbox_view.file_list.selection_set(2)
    controller._drag_start_list_idx = 1

    moved = controller.on_drag_release(SimpleNamespace(y=4))
    assert moved is True
    assert [m.key for m in model.metadata.items] == ["1", "4", "2", "3", "5"]

    controller.update_listbox()
    selected_rows = listbox_view.get_selected_indices()
    assert selected_rows == [2, 3]


def test_plain_click_on_selected_row_preserves_multiselect() -> None:
    """Verify plain click on a selected row preserves existing multi-selection."""
    model = DummyModel()
    for key in ["1", "2", "3", "4"]:
        model.metadata.add(
            ImageMeta(key=key, group="A", kind="input", nickname=f"/tmp/{key}.csv")
        )

    listbox_view = DummyListboxView()
    controller = FileListController(
        model=model,
        listbox=cast(Any, listbox_view),
        view_mode=cast(Any, DummyVar("full")),
        show_groups=cast(Any, DummyVar(False)),
        sort_key=cast(Any, DummyVar("time_imported")),
        sort_desc=cast(Any, DummyVar(False)),
    )

    controller.update_listbox()
    listbox_view.file_list.selection_set(1)
    listbox_view.file_list.selection_set(2)

    result = controller.on_click(SimpleNamespace(y=1, state=0))
    assert result == 'break'
    assert listbox_view.get_selected_indices() == [1, 2]


def test_drag_hover_row_tracks_motion_and_clears_on_release() -> None:
    """Verify drag hover indicator updates on motion and resets on release."""
    model = DummyModel()
    for key in ["1", "2", "3", "4"]:
        model.metadata.add(
            ImageMeta(key=key, group="A", kind="input", nickname=f"/tmp/{key}.csv")
        )

    listbox_view = DummyListboxView()
    controller = FileListController(
        model=model,
        listbox=cast(Any, listbox_view),
        view_mode=cast(Any, DummyVar("full")),
        show_groups=cast(Any, DummyVar(False)),
        sort_key=cast(Any, DummyVar("time_imported")),
        sort_desc=cast(Any, DummyVar(False)),
    )

    controller.update_listbox()
    controller.on_click(SimpleNamespace(y=1, state=0))
    controller.on_drag_motion(SimpleNamespace(y=35))
    assert controller._drag_hover_list_idx == 3
    assert controller._drag_hover_after is True

    controller.on_drag_release(SimpleNamespace(y=35))
    assert controller._drag_hover_list_idx is None


def test_drag_to_last_row_appends_item_to_end() -> None:
    """Verify dragging first row past end appends item to list tail."""
    model = DummyModel()
    for key in ["1", "2", "3", "4"]:
        model.metadata.add(
            ImageMeta(key=key, group="A", kind="input", nickname=f"/tmp/{key}.csv")
        )

    listbox_view = DummyListboxView()
    controller = FileListController(
        model=model,
        listbox=cast(Any, listbox_view),
        view_mode=cast(Any, DummyVar("full")),
        show_groups=cast(Any, DummyVar(False)),
        sort_key=cast(Any, DummyVar("time_imported")),
        sort_desc=cast(Any, DummyVar(False)),
    )

    controller.update_listbox()
    controller.on_click(SimpleNamespace(y=0, state=0))
    moved = controller.on_drag_release(SimpleNamespace(y=1000))

    assert moved is True
    assert [m.key for m in model.metadata.items] == ["2", "3", "4", "1"]
