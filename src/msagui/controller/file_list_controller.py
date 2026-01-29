import tkinter as tk
import os
# import Path
from tkinter.simpledialog import askstring
import pandas as pd

class FileListController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.text_bg = self.view.ListBox_1.cget('bg')  # Get the default background color of the listbox

    def on_click(self, event):
        # Handle listbox selection logic with Ctrl/Shift support
        # Get the current selection index
        index = self.view.ListBox_1.nearest(event.y)
        
        # Check whether Ctrl or Shift is pressed
        ctrl_pressed = (event.state & 0x0004) != 0  # Check for Control key
        shift_pressed = (event.state & 0x0001) != 0  # Check for Shift key

        # Handle selection logic
        if not ctrl_pressed and not shift_pressed:
            # Deselect all other items if no modifier key is pressed
            self.view.ListBox_1.selection_clear(0, tk.END)

        # If Shift is pressed, select a range of items
        if shift_pressed:
            # Get the indices of current selection
            selected_indices = self.view.ListBox_1.curselection()
            if selected_indices:
                # Select the first selected index
                start_index = selected_indices[0]
                # Select items between the last selected index and the current index
                if start_index < index:
                    self.view.ListBox_1.selection_set(start_index, index)
                else:
                    self.view.ListBox_1.selection_set(index, start_index)

        # If Ctrl is pressed, toggle the current item without affecting others
        if ctrl_pressed:
            if self.view.ListBox_1.selection_includes(index):
                self.view.ListBox_1.selection_clear(index)
            else:
                self.view.ListBox_1.selection_set(index)

        # Highlight the selected items
        self.update_selection()

    def update_selection(self):
        # Update listbox item background based on selection
        # Get the indices of selected items
        selected_indices = self.view.ListBox_1.curselection()
        for i in range(self.view.ListBox_1.size()):
            if i in selected_indices:
                self.view.ListBox_1.itemconfig(i, {'bg': 'light blue'})  # Change background color for selected
            else:
                self.view.ListBox_1.itemconfig(i, {'bg': self.text_bg})      # Reset background color for unselected

    def update_listbox(self):
        # Update the listbox display based on current view settings
        self.model.df = self.model.df.sort_values(by=["group", "fpath"], ascending=[True, True], ignore_index=True)

        self.view.ListBox_1.delete(0, tk.END)
        vsettings = self.view.get_settings()
        if self.view.show_groups.get(): # List only groups in the listbox
            max_group_number = self.model.df['group'].max()
            group_names = self.model.get_group_names()
            for i in range(max_group_number):
                self.view.ListBox_1.insert(tk.END, group_names[i])
            return
        
        desired_groups = []
        if vsettings['show_single']: # Show
            desired_groups += ['Freq1', 'Freq2', 'Freq1c', 'Freq2c', None]
        if vsettings['show_ratio']:
            desired_groups.append('Ratio')
        listbox_df = self.model.df.loc[self.model.df['type'].isin(desired_groups)]

        # Determine if column should read full path or just filename
        if (vsettings['view_mode'] == "full"):
            listbox_series = listbox_df['fpath']
        elif vsettings['view_mode'] == "parent":
            listbox_series = listbox_df['fpath'].apply(lambda x: os.path.basename(os.path.dirname(x)) + "/" + os.path.basename(x))
        elif vsettings['view_mode'] == "file":
            listbox_series = listbox_df['fname']
        else:
            print("Warning:", vsettings['view_mode'],
                    "is not a valid view mode. Defaulting to full path.")
            listbox_series = listbox_df['fpath']
        
        self.view.ListBox_1.insert(tk.END, *listbox_series.values)

        return

    def get_listbox_index(self):
        # Get currently selected listbox index
        return self.view.ListBox_1.curselection()[0]
    
    def on_file_selection(self, evt):
        # Handle listbox selection event, update display
        w = evt.widget
        if len(w.curselection()) == 0:
            return
        self.index = int(w.curselection()[0])
        value = w.get(self.index)
        self.view.Button_Filename.configure(text=os.path.basename(value))
        return
    
    def reselect_index(self):
        # Reselect and update display for current index
        # self.view.ListBox_1.select_clear(0, tk.END)  # Clear previous selection
        # self.view.ListBox_1.select_set(self.index)        # Select the specified index
        # self.view.ListBox_1.activate(self.index)          # Make it the active item
        # index = self.view.ListBox_1.curselection()
        # if len(index) == 0:
        #     return
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
        selected_indices = list(self.view.ListBox_1.curselection())
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
        if not self.view.show_groups.get():  # Check if groups are shown
            return

        selected_index = self.view.ListBox_1.curselection()
        if not selected_index:  # Check if any item is selected
            return
        
        index = selected_index[0]  # Get the first selected index
        current_value = self.view.ListBox_1.get(index)  # Get the current value
        
        # Prompt user for new name using simpledialog
        new_value = askstring("Rename Item", "Enter new name:", initialvalue=current_value)
        if new_value is not None:  # Check if user didn't cancel
            self.model.set_group_name(new_value, index+1)  # Set the new name
        self.update_listbox()
        return