import logging
import tkinter as tk
import os
# import Path
from tkinter.simpledialog import askstring
import pandas as pd
from msagui.view.display import ListboxView, ViewDefaults
from msagui.view.defaults import ViewDefaults

logger = logging.getLogger(__name__)

class FileListController:
    def __init__(self, model, listbox: ListboxView, view_mode: tk.StringVar | None = None,
                 show_groups: tk.BooleanVar | None = None):
        self.model = model
        self.listbox = listbox
        self.view_mode = view_mode
        self.show_groups = show_groups
        self.text_bg = ViewDefaults.bg
        self.index = None
        self._group_ids: list = []  # group IDs in listbox order when in group view

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
        # Handle listbox selection logic with Ctrl/Shift support
        # Get the current selection index
        index = self.listbox.file_list.nearest(event.y)
        
        # Check whether Ctrl or Shift is pressed
        ctrl_pressed = (event.state & 0x0004) != 0  # Check for Control key
        shift_pressed = (event.state & 0x0001) != 0  # Check for Shift key

        # Handle selection logic
        if not ctrl_pressed and not shift_pressed:
            # Deselect all other items if no modifier key is pressed
            self.listbox.file_list.selection_clear(0, tk.END)

        # If Shift is pressed, select a range of items
        if shift_pressed:
            # Get the indices of current selection
            selected_indices = self.listbox.file_list.curselection()
            if selected_indices:
                # Select the first selected index
                start_index = selected_indices[0]
                # Select items between the last selected index and the current index
                if start_index < index:
                    self.listbox.file_list.selection_set(start_index, index)
                else:
                    self.listbox.file_list.selection_set(index, start_index)

        # If Ctrl is pressed, toggle the current item without affecting others
        if ctrl_pressed:
            if self.listbox.file_list.selection_includes(index):
                self.listbox.file_list.selection_clear(index)
            else:
                self.listbox.file_list.selection_set(index)

        # Highlight the selected items
        self.update_selection()

    def update_selection(self):
        # Update listbox item background based on selection
        # Get the indices of selected items
        selected_indices = self.listbox.file_list.curselection()
        for i in range(self.listbox.file_list.size()):
            if i in selected_indices:
                self.listbox.file_list.itemconfig(i, {'bg': 'light blue'})  # Change background color for selected
            else:
                self.listbox.file_list.itemconfig(i, {'bg': self.text_bg})      # Reset background color for unselected

    def update_listbox(self):
        # Update the listbox display based on current view settings
        if self.show_groups is not None and self.show_groups.get():
            groups = [g for g in self.model.metadata.groups(visible_only=True) if g != "default"]
            self._group_ids = groups
            display_names = [self._group_display_name(g) for g in groups]
            logger.info(f"Updating listbox with groups: {display_names}")
            self.listbox.update(display_names)
            self.reselect_index()
            return

        self._group_ids = []
        mode = self.view_mode.get() if self.view_mode is not None else "full"
        nicknames = self.model.metadata.nicknames(visible_only=True)
        display_names = [self._format_name(n, mode) for n in nicknames]
        logger.info(f"Updating listbox with display_names (mode={mode!r}): {display_names}")
        self.listbox.update(display_names)
        self.reselect_index()
        return
        self.listbox.file_list.delete(0, tk.END)

        # vsettings = self.view.get_settings()
        # if self.view.show_groups.get(): # List only groups in the listbox
        #     max_group_number = self.model.df['group'].max()
        #     group_names = self.model.get_group_names()
        #     for i in range(max_group_number):
        #         self.view.file_list.insert(tk.END, group_names[i])
        #     return
        
        # desired_groups = []
        # if vsettings['show_single']: # Show
        #     desired_groups += ['Freq1', 'Freq2', 'Freq1c', 'Freq2c', None]
        # if vsettings['show_ratio']:
        #     desired_groups.append('Ratio')
        # listbox_df = self.model.df.loc[self.model.df['type'].isin(desired_groups)]

        # # Determine if column should read full path or just filename
        # if (vsettings['view_mode'] == "full"):
        #     listbox_series = listbox_df['fpath']
        # elif vsettings['view_mode'] == "parent":
        #     listbox_series = listbox_df['fpath'].apply(lambda x: os.path.basename(os.path.dirname(x)) + "/" + os.path.basename(x))
        # elif vsettings['view_mode'] == "file":
        #     listbox_series = listbox_df['fname']
        # else:
        #     print("Warning:", vsettings['view_mode'],
        #             "is not a valid view mode. Defaulting to full path.")
        #     listbox_series = listbox_df['fpath']
        
        self.listbox.file_list.insert(tk.END, *keys)

        return

    def get_listbox_index(self):
        # Get currently selected listbox index; returns group_id in group view mode
        idx = self.listbox.get_selected_indices()
        if len(idx) == 0:
            return
        listbox_pos = int(idx[0])
        if self.show_groups is not None and self.show_groups.get() and self._group_ids:
            return self._group_ids[listbox_pos]
        return listbox_pos
        # value = self.view.file_list.get(idx)
    
    def on_file_selection(self, evt) -> str:
        # Handle listbox selection event, update display
        w = evt.widget
        idx = self.listbox.get_selected_indices()
        print(f"[ListboxController.py | onf] Selected indices: {idx}")
        if len(idx) == 0:
            return ''
        self.index = int(idx[0])
        value = w.get(self.index)
        return value
    
    def reselect_index(self):
        print(f"[ListboxController.py] Reselecting index: {self.index}")
        if self.index is None:
            return
        # Reselect and update display for current index
        self.listbox.file_list.select_clear(0, tk.END)  # Clear previous selection
        self.listbox.file_list.select_set(self.index)        # Select the specified index
        self.listbox.file_list.activate(self.index)          # Make it the active item
        index = self.listbox.file_list.curselection()
        if len(index) == 0:
            return
        return

    def convert_index(self, index: int) -> pd.Index:
        """Convert listbox index to dataframe index by sorting out single wavenumber,
        ratio, or histograms if needbe. Return array of indices if group is selected"""
        if self.view.show_groups.get(): #TODO Check: May need to convert to listbox type to integer
            group = self.get_listbox_index()
            idx = self.model.df['group'] == group + 1
            single_group_df = self.model.df.loc[idx,:]
            df_idx = single_group_df.index
            return df_idx.tolist()

        # Create dataframe that mimics what is shown in the listbox
        viewed_types = []
        if self.view.show_single.get():
            viewed_types += ['Freq1', 'Freq2', 'Freq1c', 'Freq2c', None]
        if self.view.show_ratio.get():
            viewed_types.append('Ratio')
        listbox_df = self.model.df.loc[self.model.df['type'].isin(viewed_types)]
        df_idx = listbox_df.index[index]
        # Return the index of the dataframe that corresponds to the index of the listbox
        return df_idx.tolist()
    
    def get_df_indices(self):
        # Get dataframe indices corresponding to selected listbox items
        # Mimic the listbox view with a dataframe slice
        selected_indices = list(self.listbox.file_list.curselection())
        vsettings = self.view.get_settings()
        desired_groups = []
        if vsettings['show_single']: # Show
            desired_groups += ['Freq1', 'Freq2', 'Freq1c', 'Freq2c', None]
        if vsettings['show_ratio']:
            desired_groups.append('Ratio')
        listbox_df = self.model.df.loc[self.model.df['type'].isin(desired_groups)]
        # Select positional indices in dataframe from the listbox
        selection = listbox_df.iloc[selected_indices,:]
        # Return real dataframe indices
        return selection.index
    
    def rename_item(self, event):
        # Allow renaming of group items in the listbox
        if not self.listbox.show_groups.get():  # Check if groups are shown
            return

        selected_index = self.listbox.file_list.curselection()
        if not selected_index:  # Check if any item is selected
            return
        
        index = selected_index[0]  # Get the first selected index
        current_value = self.listbox.file_list.get(index)  # Get the current value
        
        # Prompt user for new name using simpledialog
        new_value = askstring("Rename Item", "Enter new name:", initialvalue=current_value)
        if new_value is not None:  # Check if user didn't cancel
            self.model.set_group_name(new_value, index+1)  # Set the new name
        self.listbox.update()
        return