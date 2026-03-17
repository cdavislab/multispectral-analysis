from tkinter.filedialog import askopenfilename, askopenfilenames, asksaveasfilename
import csv
import os
import json
import tkinter as tk
from msagui.view.progress_bar import ProgressBar

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
        # Import a list of files from a CSV produced by export_filelist and add them
        file_of_files = askopenfilenames(filetypes=(("CSV files", "*.csv"), ("All files", "*.*"),))
        if len(file_of_files) == 0:
            return
        with open(file_of_files[0], newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            filelist = [row["fpath"] for row in reader]
        with ProgressBar(title="Adding Files", total=len(filelist)) as progress:
            self.model.add(filelist, progress_callback=progress.step)
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
            "show_inputs":     self.view.show_inputs,
            "show_outputs":    self.view.show_outputs,
        }
        for key, var in bool_vars.items():
            if key in view_settings:
                var.set(bool(view_settings[key]))

        if "show_inputs" not in view_settings and "show_single" in view_settings:
            self.view.show_inputs.set(bool(view_settings["show_single"]))
        if "show_outputs" not in view_settings and "show_ratio" in view_settings:
            self.view.show_outputs.set(bool(view_settings["show_ratio"]))

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

    def _build_settings_dict(self) -> dict:
        """Build the settings dict from current model and view state."""
        return {
            "imaging": self.model.settings.to_dict(),
            "view": {
                "show_groups":     self.view.show_groups.get(),
                "show_histograms": self.view.show_histograms.get(),
                "show_inputs":     self.view.show_inputs.get(),
                "show_outputs":    self.view.show_outputs.get(),
            },
        }

    def export_settings(self):
        """Export ImagingSettings and view state to a JSON file chosen by the user."""
        file_path = asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export Settings As",
        )
        if not file_path:
            return

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self._build_settings_dict(), f, indent=2)

    def export_default_settings(self):
        """Save current settings as the default (msa_options.json in the working directory)."""
        with open("msa_options.json", "w", encoding="utf-8") as f:
            json.dump(self._build_settings_dict(), f, indent=2)
        tk.messagebox.showinfo("Default Settings", "Settings saved as default (msa_options.json).")