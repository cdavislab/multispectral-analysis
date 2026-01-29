from tkinter.filedialog import askopenfilename, askopenfilenames, asksaveasfilename
import pandas as pd
import os
import tkinter as tk

class DropDownController:
    def __init__(self, model, view):
        self.model = model
        self.view = view

    def export_stats(self):
        # Export statistics using the model
        self.model.export_stats()

    def export_filelist(self):
        # Export current file list to a text file
        file_path = asksaveasfilename(
            defaultextension=".txt",  # Default file extension
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],  # Supported file types
            title="Save Settings As"
        )
        if file_path == '':  # If the user cancels the save dialog, return
            return
        
        self.model.export_filelist(file_path)

    def import_filelist(self):
        # Import a list of files from a file and add them
        progress = self.view.ProgressBar(title="Adding Files")
        file_of_files = askopenfilenames(filetypes=(("Comma Delimited", "*.txt"), ("All files", "*.*"),))
        if len(file_of_files) == 0:
            progress.destroy()
            return
        file_df = pd.read_csv(file_of_files[0])
        file_df = file_df[~file_df.applymap(lambda x: isinstance(x, str) and "ratio" in x.lower()).any(axis=1)]
        filelist = file_df['fpath'].tolist()
        self.add_files(filelist, progress)
        return
    
    def import_settings(self, file_path = None):
        # Import settings from a file and update UI/model
        if file_path == None:
            file_path = askopenfilename(
            defaultextension=".txt",  # Default file extension
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],  # Supported file types
            title="Save Settings As"
        )
        if file_path == '':  # If the user cancels the save dialog, return
            return
        
        # Read dictionary from the text file
        with open(file_path, 'r', encoding='utf-8') as file:
            settings = eval(file.read())

        entries = {
            'freq1': self.view.entries['freq1'],
            'freq2': self.view.entries['freq2'],
            'freq1c': self.view.entries['freq1c'],
            'freq2c': self.view.entries['freq2c'],
            'freq1cf': self.view.entries['freq1cf'],
            'freq2cf': self.view.entries['freq2cf'],
            'threshold': self.view.entries['threshold']
        }

        for key, entry in entries.items():
            if key in settings:
                entry.delete(0, tk.END)  # Clear the entry
                entry.insert(0, settings.get(key, ''))  # Insert new value

        if 'export_folder' in settings:
            self.view.Button_ExportFolder['text'] = settings.get('export_folder', '')
            self.model.set_pref('export_folder', settings.get('export_folder', ''))

        # Set boolean variables based on the settings dictionary
        # TODO: Put this in model
        self.view.show_groups.set(settings.get('show_groups', False))
        self.view.show_single.set(settings.get('show_single', True))
        self.view.show_ratio.set(settings.get('show_ratio', True))
        self.view.show_histograms.set(settings.get('show_histograms', False))

        self.model.set_pref('filetype', settings.get('export_filetype', '.jpg'))

        # Set view_length if the key exists
        self.view_length = settings.get('view_mode', 'full')

        for key in self.img_config:
            if key in settings:
                self.model.set_pref(key,settings[key])
        
        self.update_listbox()


    def import_default_settings(self):
        # Import default settings from file if available
        if not os.path.exists('msa_options.txt'):
            self.model.set_pref('filetype','.jpg')
            return
        # # Get the absolute path of the currently running Python file
        # current_file_path = os.path.abspath(__file__)

        # # Remove the file name and append 'msa_options.txt'
        # directory_path = os.path.dirname(current_file_path)
        # default = os.path.join(directory_path, 'msa_options.txt')
        self.import_settings('msa_options.txt')
        return
    
    def toggle_checkbox(self, checkbox):
        # Toggle a Tkinter BooleanVar checkbox
        if checkbox.get():
            checkbox.set(False)
        else:
            checkbox.set(True)
        return
    
    def export_settings(self):
        # Export current settings to a text file
        file_path = asksaveasfilename(
        defaultextension=".txt",  # Default file extension
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],  # Supported file types
        title="Save Settings As"
    )
        if file_path == '':  # If the user cancels the save dialog, return
            return

        settings = self.view.get_settings()
        settings.update(self.model.get_preferences())
        # Save dictionary to a text file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(repr(settings))

        return