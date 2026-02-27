from tkinter.filedialog import askopenfilename, askopenfilenames, asksaveasfilename
import pandas as pd
import os
import json
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
    
    def import_settings(self, file_path=None):
        """Import settings from a JSON file and apply them to the model and view."""
        if file_path is None:
            file_path = askopenfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Import Settings",
            )
        if not file_path or not os.path.exists(file_path):
            return

        with open(file_path, "r", encoding="utf-8") as f:
            settings = json.load(f)

        # Apply imaging settings to the model dataclass.
        if "imaging" in settings:
            self.model.settings.update_from_dict(settings["imaging"])

        # Apply view-state toggles if present.
        view_settings = settings.get("view", {})
        bool_vars = {
            "show_groups":     self.view.show_groups,
            "show_histograms": self.view.show_histograms,
            "show_single":     self.view.show_single,
            "show_ratio":      self.view.show_ratio,
        }
        for key, var in bool_vars.items():
            if key in view_settings:
                var.set(bool(view_settings[key]))

    def import_default_settings(self):
        """Import default settings from 'msa_options.json' if it exists."""
        if os.path.exists("msa_options.json"):
            self.import_settings("msa_options.json")

    def toggle_checkbox(self, checkbox):
        # Toggle a Tkinter BooleanVar checkbox
        if checkbox.get():
            checkbox.set(False)
        else:
            checkbox.set(True)
        return

    def export_settings(self):
        """Export ImagingSettings and view state to a JSON file chosen by the user."""
        file_path = asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export Settings As",
        )
        if not file_path:
            return

        settings = {
            "imaging": self.model.settings.to_dict(),
            "view": {
                "show_groups":     self.view.show_groups.get(),
                "show_histograms": self.view.show_histograms.get(),
                "show_single":     self.view.show_single.get(),
                "show_ratio":      self.view.show_ratio.get(),
            },
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)

        return