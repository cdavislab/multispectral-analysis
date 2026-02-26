
from tkinter.filedialog import askopenfilenames, askdirectory
import tkinter as tk
import tkinter.messagebox as messagebox
import os
from msagui.view.progress_bar import ProgressBar

class ButtonsController:
    def __init__(self, model, view):
        self.model = model
        self.view = view

    def add(self):
        files = askopenfilenames(
            filetypes=(("Comma Delimited", "*.csv"), ("All files", "*.*"))
        )
        if not files:
            return

        with ProgressBar(title="Processing", total=len(files)) as progress:
            results = self.model.add(files, progress_callback=progress.step)

        if len(results.keys()) != 0:
            self.view.show_error(results)
        
    def delete(self):
        # Delete selected files from listbox and model
        idx_to_del = self.view.listbox.get_selected_indices()
        if not idx_to_del:
            return

        with ProgressBar(title="Deleting Files", total=len(idx_to_del)) as progress:
            results = self.model.delete(idx_to_del, progress_callback=progress.step)

        if len(results.keys()) != 0:
            self.view.show_error(results)


    #TODO: Troubleshoot addition of dictionaries and swap to freq1 vs lw
    def validate_entries(self):
        # Validate user input fields before analysis
        # Ignore analyze request if no files are loaded
        if self.model.df.empty:
            messagebox.showerror("Add Files", "Add files using \"Add Files\" button before analyzing.")
            return None
        if self.view.show_groups.get():
            messagebox.showerror("Group View", "Cannot analyze in group view.")
            return None
        if not self.view.show_single.get():
            messagebox.showerror("Single Wavenumber", "Please select at least two non-ratio images to analyze.")
            return None
        # Get the values from the entries
        entry_keys = ('freq1', 'freq2', 'freq1c', 'freq2c', 'threshold', 'freq1cf', 'freq2cf')
        args = self.view.get_settings()
        args = {key: args[key] for key in entry_keys}
        # Check if required fields are empty
        if any(args[key] == '' for key in ['freq1', 'freq2']):
            messagebox.showerror("Missing Fields", "Please fill out all fields before analyzing.")
            return None
        # Convert the string inputs to floats
        for key in ['threshold','freq1cf', 'freq2cf']:
            s = args[key]
            try:
                args[key] = float(s) if s.strip() else 0.0
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter an integer or decimal for the number of wavenumbers.")
                return None
            
        
        # If the correction factor is non-zero, but no correction factor label is entered, show an error
        if ('' == args['freq1c']) and (args['freq1cf'] != 0):
            messagebox.showerror("Missing Fields", "Please enter a label for Frequency 1 Correction.")
            return None
        if ('' == args['freq2c']) and (args['freq2cf'] != 0):
            messagebox.showerror("Missing Fields", "Please enter a label for Frequency 2 Correction.")
            return None
        # If the correction factor for frequency is 0, set correction factor label to None
        if args['freq1cf'] == 0:
            args['freq1c'] = None
        if args['freq2cf'] == 0:
            args['freq2c'] = None
        # If the view has multiple corrections/factors, add them to args
        if hasattr(self.view, 'multiple_corrections') and hasattr(self.view, 'multiple_factors'):
            args['multiple_corrections'] = self.view.multiple_corrections
            args['multiple_factors'] = self.view.multiple_factors
        return args

    def count_unique_types(self, entries):
        # Count unique types among frequency/correction entries
        types = set([entries['freq1'],
                 entries['freq2'],
                 entries['freq1c'],
                 entries['freq2c']])
        if None in types:
            types.remove(None)
        return len(types)

    def group(self):
        self.model.set_keywords()
        self.model.set_groups()

    def analyze(self):
        selected_idx = self.view.listbox.get_selected_indices()
        if not selected_idx:
            messagebox.showerror("No Selection", "Please select at least one file to analyze.")
            return
        with ProgressBar(title="Analyzing", total=len(selected_idx)) as progress:
            error = self.model.analyze(selected_idx, progress_callback=progress)
            messagebox.showerror("Analysis Error", error) if error else None

    def set_export_folder(self):
        # Set export folder and optionally move files there
        directory = askdirectory()
        self.model.settings.export_directory = directory
        self.view.set_button_text('Export Folder', directory)
        
        if len(self.model.metadata.keys) != 0:
            self.move_files_to_export()
        
        return

    def move_files_to_export(self):
        # Move all exported files to the new export folder
        # Prompt user if they want to move the files to the new export folder
        if not messagebox.askyesno("Move Files", "Would you like to move the files to the new export folder?"):
            return
        # If the user selects yes, move the files to the new export folder
        # Take all of the img_path and hist_path files and move them to the new export folder
        for i in range(len(self.model.df)):
            try:
                img_path = self.model.df.loc[i, 'im_path']
                hist_path = self.model.df.loc[i, 'hist_path']
                img_path_new = os.path.join(self.model.get_pref('export_folder'), os.path.basename(img_path))
                hist_path_new = os.path.join(self.model.get_pref('export_folder'), os.path.basename(hist_path))
                os.rename(img_path, img_path_new)
                os.rename(hist_path, hist_path_new)
                self.model.df.loc[i, 'im_path'] = img_path_new
                self.model.df.loc[i, 'hist_path'] = hist_path_new
            except Exception as e:
                messagebox.showerror("Error", f"Error moving file: {e}")
        
        # Check if the model has groups
        if not (hasattr(self.model, 'group_images') and hasattr(self.model, 'group_histograms')):
            return

        # Move the group and histogram files located in the varirables self.model.group_images and self.model.group_histograms
        for i in range(len(self.model.group_images)):
            try:
                group_path = self.model.group_images[i]
                group_path_new = os.path.join(self.model.get_pref('export_folder'), os.path.basename(group_path))
                os.rename(group_path, group_path_new)
                self.model.group_images[i] = group_path_new
            except Exception as e:
                messagebox.showerror("Error", f"Error moving file: {e}")
        #Do the same for self.model.group_histograms
        for i in range(len(self.model.group_histograms)):
            try:
                group_path = self.model.group_histograms[i]
                group_path_new = os.path.join(self.model.get_pref('export_folder'), os.path.basename(group_path))
                os.rename(group_path, group_path_new)
                self.model.group_histograms[i] = group_path_new
            except Exception as e:
                messagebox.showerror("Error", f"Error moving file: {e}")
        return