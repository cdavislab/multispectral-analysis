import logging
import tkinter as tk
import os
from tkinter.simpledialog import askstring
from msagui.view.display import ListboxView, ViewDefaults

logger = logging.getLogger(__name__)

class FileListController:
    def __init__(self, model, listbox: ListboxView, view_mode: tk.StringVar | None = None,
                 show_groups: tk.BooleanVar | None = None,
                 sort_key: tk.StringVar | None = None,
                 sort_desc: tk.BooleanVar | None = None):
        self.model = model
        self.listbox = listbox
        self.view_mode = view_mode
        self.show_groups = show_groups
        self.sort_key = sort_key
        self.sort_desc = sort_desc
        self.text_bg = ViewDefaults.bg
        self.index = None
        self._group_ids: list = []
        self._visible_indices: list[int] = []
        self._selected_key: str | None = None
        self._selected_keys: list[str] = []
        self._selected_group_id = None
        self._pending_selected_key: str | None = None
        self._pending_selected_keys: list[str] | None = None
        self._drag_start_list_idx: int | None = None
        self._drag_hover_list_idx: int | None = None
        self._drag_hover_after: bool = False

    def _group_display_name(self, group_id) -> str:
        """Return a display name for the group, respecting the current view mode."""
        items = self.model.metadata.by_group(group_id)
        if not items or not items[0].common_name:
            return f"Group {group_id}"
        mode = self.view_mode.get() if self.view_mode is not None else "full"
        item = items[0]
        formatted = self._format_name(item.nickname, mode)
        if item.keyword:
            formatted = formatted.replace(item.keyword, "")
        return formatted

    @staticmethod
    def _format_name(nickname: str, mode: str) -> str:
        """Return the display string for *nickname* according to *mode*."""
        if mode == "parent":
            parent = os.path.basename(os.path.dirname(nickname))
            base = os.path.basename(nickname)
            return f"{parent}/{base}" if parent else base
        if mode == "file":
            return os.path.basename(nickname)
        return nickname  # "full"

    def on_click(self, event):
        index = self.listbox.file_list.nearest(event.y)
        ctrl_pressed = (event.state & 0x0004) != 0  # Check for Control key
        shift_pressed = (event.state & 0x0001) != 0  # Check for Shift key
        selected_indices = tuple(self.listbox.file_list.curselection())
        clicked_is_selected = index in selected_indices

        if self.show_groups is None or not self.show_groups.get():
            if not ctrl_pressed and not shift_pressed:
                self._drag_start_list_idx = index
            else:
                self._drag_start_list_idx = None
        else:
            self._drag_start_list_idx = None

        if not ctrl_pressed and not shift_pressed and clicked_is_selected and len(selected_indices) > 1:
            self.update_selection()
            self.listbox.file_list.event_generate('<<ListboxSelect>>')
            return 'break'

        if not ctrl_pressed and not shift_pressed:
            self.listbox.file_list.selection_clear(0, tk.END)
            self.listbox.file_list.selection_set(index)

        if shift_pressed:
            if selected_indices:
                start_index = selected_indices[0]
                if start_index < index:
                    self.listbox.file_list.selection_set(start_index, index)
                else:
                    self.listbox.file_list.selection_set(index, start_index)

        if ctrl_pressed:
            if self.listbox.file_list.selection_includes(index):
                self.listbox.file_list.selection_clear(index)
            else:
                self.listbox.file_list.selection_set(index)

        self.update_selection()
        self.listbox.file_list.event_generate('<<ListboxSelect>>')
        return 'break'

    def update_selection(self):
        selected_indices = self.listbox.file_list.curselection()
        for i in range(self.listbox.file_list.size()):
            if i in selected_indices:
                self.listbox.file_list.itemconfig(i, {'bg': 'light blue'})
            else:
                self.listbox.file_list.itemconfig(i, {'bg': self.text_bg})

        if (
            self._drag_hover_list_idx is not None
            and 0 <= self._drag_hover_list_idx < self.listbox.file_list.size()
            and self._drag_hover_list_idx not in selected_indices
        ):
            hover_color = 'khaki3' if self._drag_hover_after else 'khaki1'
            self.listbox.file_list.itemconfig(self._drag_hover_list_idx, {'bg': hover_color})

    def _drop_insert_row(self, y: int) -> int:
        """Return insertion row in [0, size], where size means append to end."""
        size = len(self._visible_indices)
        if size == 0:
            return 0

        nearest_row = self.listbox.file_list.nearest(y)
        nearest_row = max(0, min(nearest_row, size - 1))

        after = False
        try:
            bbox = self.listbox.file_list.bbox(nearest_row)
            if bbox:
                row_y, row_h = int(bbox[1]), int(bbox[3])
                after = y >= (row_y + row_h / 2)
            else:
                after = nearest_row == size - 1 and y > nearest_row
        except Exception:
            after = nearest_row == size - 1 and y > nearest_row

        if after:
            return min(size, nearest_row + 1)
        return nearest_row

    def select_all(self, event=None):
        self.listbox.file_list.selection_set(0, tk.END)
        self.update_selection()
        return 'break'

    def _remember_selection(self):
        if self._pending_selected_keys is not None:
            self._selected_keys = self._pending_selected_keys[:]
            self._selected_key = self._selected_keys[0] if self._selected_keys else None
            self._pending_selected_keys = None
            self._pending_selected_key = None
            return

        if self._pending_selected_key is not None:
            self._selected_key = self._pending_selected_key
            self._selected_keys = [self._pending_selected_key]
            self._pending_selected_key = None
            return

        selected = self.listbox.get_selected_indices()
        if not selected:
            self._selected_key = None
            self._selected_keys = []
            self._selected_group_id = None
            return

        list_idx = selected[0]
        if self.show_groups is not None and self.show_groups.get():
            if list_idx < len(self._group_ids):
                self._selected_group_id = self._group_ids[list_idx]
            self._selected_keys = []
            return

        selected_keys = []
        for row in selected:
            if row < len(self._visible_indices):
                metadata_idx = self._visible_indices[row]
                if metadata_idx < len(self.model.metadata.items):
                    selected_keys.append(self.model.metadata.items[metadata_idx].key)
        self._selected_keys = selected_keys
        self._selected_key = selected_keys[0] if selected_keys else None

    def _reselect_saved_selection(self):
        self.listbox.file_list.selection_clear(0, tk.END)

        if self.show_groups is not None and self.show_groups.get():
            if self._selected_group_id in self._group_ids:
                row = self._group_ids.index(self._selected_group_id)
                self.listbox.file_list.selection_set(row)
                self.listbox.file_list.activate(row)
                self.index = row
            self.update_selection()
            return

        if not self._selected_keys:
            self.update_selection()
            return

        first_row = None
        for key in self._selected_keys:
            metadata_idx = None
            for i, meta in enumerate(self.model.metadata.items):
                if meta.key == key:
                    metadata_idx = i
                    break
            if metadata_idx is None or metadata_idx not in self._visible_indices:
                continue
            row = self._visible_indices.index(metadata_idx)
            self.listbox.file_list.selection_set(row)
            if first_row is None:
                first_row = row

        if first_row is not None:
            self.listbox.file_list.activate(first_row)
            self.index = first_row
        self.update_selection()

    def update_listbox(self):
        self._remember_selection()

        if self.show_groups is not None and self.show_groups.get():
            groups = [g for g in self.model.metadata.groups(visible_only=True) if g != "default"]
            self._visible_indices = []
            self._group_ids = groups
            display_names = [self._group_display_name(g) for g in groups]
            logger.info(f"Updating listbox with groups: {display_names}")
            self.listbox.update(display_names)
            self._reselect_saved_selection()
            return

        self._group_ids = []
        self._selected_group_id = None
        self._visible_indices = self.model.metadata.visible_indices()
        mode = self.view_mode.get() if self.view_mode is not None else "full"
        display_names = [
            self._format_name(self.model.metadata.items[idx].nickname, mode)
            for idx in self._visible_indices
        ]
        logger.info(f"Updating listbox with display_names (mode={mode!r}): {display_names}")
        self.listbox.update(display_names)
        self._reselect_saved_selection()
        return

    def get_listbox_index(self):
        idx = self.listbox.get_selected_indices()
        if len(idx) == 0:
            return
        listbox_pos = int(idx[0])
        if self.show_groups is not None and self.show_groups.get() and self._group_ids:
            return self._group_ids[listbox_pos]
        if listbox_pos >= len(self._visible_indices):
            return
        return self._visible_indices[listbox_pos]

    def get_selected_metadata_indices(self) -> list[int]:
        if self.show_groups is not None and self.show_groups.get():
            return []
        rows = self.listbox.get_selected_indices()
        indices = []
        for row in rows:
            if row < len(self._visible_indices):
                indices.append(self._visible_indices[row])
        return indices

    def get_selected_group_ids(self) -> list:
        if self.show_groups is None or not self.show_groups.get():
            return []
        rows = self.listbox.get_selected_indices()
        group_ids = []
        for row in rows:
            if row < len(self._group_ids):
                group_ids.append(self._group_ids[row])
        return group_ids
    
    def on_file_selection(self, evt) -> str:
        w = evt.widget
        idx = self.listbox.get_selected_indices()
        print(f"[ListboxController.py | onf] Selected indices: {idx}")
        if len(idx) == 0:
            return ''
        self.index = int(idx[0])
        if self.show_groups is not None and self.show_groups.get() and self._group_ids:
            self._selected_group_id = self._group_ids[self.index]
            self._selected_key = None
            self._selected_keys = []
        elif self.index < len(self._visible_indices):
            metadata_idx = self._visible_indices[self.index]
            self._selected_key = self.model.metadata.items[metadata_idx].key
            selected_rows = self.listbox.get_selected_indices()
            self._selected_keys = []
            for row in selected_rows:
                if row < len(self._visible_indices):
                    idx2 = self._visible_indices[row]
                    if idx2 < len(self.model.metadata.items):
                        self._selected_keys.append(self.model.metadata.items[idx2].key)
            self._selected_group_id = None
        value = w.get(self.index)
        return value

    def on_drag_release(self, event):
        if self.show_groups is not None and self.show_groups.get():
            self._drag_start_list_idx = None
            self._drag_hover_list_idx = None
            self._drag_hover_after = False
            self.update_selection()
            return False

        if self._drag_start_list_idx is None:
            self._drag_hover_list_idx = None
            self._drag_hover_after = False
            self.update_selection()
            return False

        from_row = self._drag_start_list_idx
        insert_row = self._drop_insert_row(event.y)
        self._drag_start_list_idx = None
        self._drag_hover_list_idx = None
        self._drag_hover_after = False

        if insert_row < 0 or insert_row > len(self._visible_indices):
            self.update_selection()
            return False
        if from_row < 0 or from_row >= len(self._visible_indices):
            self.update_selection()
            return False

        selected_rows = sorted(set(self.listbox.get_selected_indices()))
        if selected_rows and from_row in selected_rows:
            moving_rows = [row for row in selected_rows if row < len(self._visible_indices)]
        else:
            moving_rows = [from_row]

        if not moving_rows:
            self.update_selection()
            return False

        if insert_row >= moving_rows[0] and insert_row <= (moving_rows[-1] + 1):
            self.update_selection()
            return False

        from_meta_indices = [self._visible_indices[row] for row in moving_rows]
        if insert_row == len(self._visible_indices):
            to_meta_idx = len(self.model.metadata.items)
        else:
            to_meta_idx = self._visible_indices[insert_row]
        original_keys = [self.model.metadata.items[idx].key for idx in from_meta_indices]
        moved = self.model.metadata.move_items(from_meta_indices, to_meta_idx)
        if not moved:
            self.update_selection()
            return False

        if not original_keys:
            if to_meta_idx < len(self.model.metadata.items):
                original_keys = [self.model.metadata.items[to_meta_idx].key]
            elif self.model.metadata.items:
                original_keys = [self.model.metadata.items[-1].key]

        self._pending_selected_keys = original_keys
        self._pending_selected_key = original_keys[0]
        self.update_selection()
        return True

    def on_drag_motion(self, event):
        if self.show_groups is not None and self.show_groups.get():
            return
        if self._drag_start_list_idx is None:
            return
        if len(self._visible_indices) == 0:
            return

        insert_row = self._drop_insert_row(event.y)
        if insert_row <= 0:
            hover_row = 0
            hover_after = False
        elif insert_row >= len(self._visible_indices):
            hover_row = len(self._visible_indices) - 1
            hover_after = True
        else:
            hover_row = insert_row
            hover_after = False

        if hover_row != self._drag_hover_list_idx or hover_after != self._drag_hover_after:
            self._drag_hover_list_idx = hover_row
            self._drag_hover_after = hover_after
            self.update_selection()

    def sort_items(self):
        sort_key = self.sort_key.get() if self.sort_key is not None else "time_imported"
        reverse = bool(self.sort_desc.get()) if self.sort_desc is not None else False

        self._remember_selection()
        self.model.metadata.sort_items(sort_key=sort_key, reverse=reverse)

    def rename_item(self, event):
        if self.show_groups is None or not self.show_groups.get():
            return

        selected_index = self.listbox.file_list.curselection()
        if not selected_index:
            return

        index = selected_index[0]
        current_value = self.listbox.file_list.get(index)

        new_value = askstring("Rename Item", "Enter new name:", initialvalue=current_value)
        if new_value is not None:
            self.model.set_group_name(new_value, index+1)
        self.update_listbox()
        return