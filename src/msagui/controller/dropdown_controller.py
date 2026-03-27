from tkinter.filedialog import askopenfilename, askopenfilenames, asksaveasfilename
import csv
import os
import json
import platform
import tempfile
import logging
import tkinter as tk
import tkinter.messagebox as messagebox
from datetime import datetime
from typing import Any
from msagui.view.progress_bar import ProgressBar
from msagui.model.logging_utils import export_logs_bundle

logger = logging.getLogger(__name__)

class DropDownController:
    def __init__(self, model: Any, view: Any) -> None:
        self.model = model
        self.view = view
        self.default_settings_path = self._resolve_default_settings_path()

    def _resolve_default_settings_path(self) -> str:
        home = os.path.expanduser("~")
        system = platform.system()

        if system == "Windows":
            base_dir = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or home
            app_dir = os.path.join(base_dir, "msaGUI")
        elif system == "Darwin":
            app_dir = os.path.join(home, "Library", "Application Support", "msaGUI")
        else:
            base_dir = os.environ.get("XDG_CONFIG_HOME") or os.path.join(home, ".config")
            app_dir = os.path.join(base_dir, "msaGUI")

        try:
            os.makedirs(app_dir, exist_ok=True)
            return os.path.join(app_dir, "msa_options.json")
        except OSError:
            return os.path.join(tempfile.gettempdir(), "msaGUI_msa_options.json")

    def export_stats(self) -> None:
        # Export statistics using the model
        self.model.export_stats()

    def export_filelist(self) -> None:
        # Export current file list to a CSV file
        file_path = asksaveasfilename(
            defaultextension=".csv",  # Default file extension
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],  # Supported file types
            title="Save File List As"
        )
        if file_path == '':  # If the user cancels the save dialog, return
            return
        
        self.model.export_filelist(file_path)

    def save_session_as(self) -> None:
        """Export the current working session to an HDF5 file."""
        file_path = asksaveasfilename(
            defaultextension=".h5",
            filetypes=[
                ("HDF5 files (*.h5)", "*.h5"),
                ("HDF5 files (*.hdf5)", "*.hdf5"),
                ("All files", "*.*"),
            ],
            title="Save Session As",
            initialfile="msa_session.h5",
        )
        if not file_path:
            return

        root, ext = os.path.splitext(file_path)
        if ext == "":
            file_path = f"{root}.h5"

        view_state = {
            "show_groups": self.view.show_groups.get(),
            "show_histograms": self.view.show_histograms.get(),
            "show_inputs": self.view.show_inputs.get(),
            "show_outputs": self.view.show_outputs.get(),
            "view_mode": self.view.view_mode.get(),
            "sort_key": self.view.sort_key.get(),
            "sort_desc": self.view.sort_desc.get(),
        }

        try:
            saved_path = self.model.save_session(file_path, view_state=view_state)
            messagebox.showinfo("Session Saved", f"Session exported to:\n{saved_path}")
        except Exception:
            logger.exception("Failed to export session")
            messagebox.showerror(
                "Session Export Failed",
                "Could not export session. Please try a different location and try again.",
            )

    def load_session(self) -> None:
        """Load a previously exported session from an HDF5 file."""
        file_path = askopenfilename(
            defaultextension=".h5",
            filetypes=[
                ("HDF5 files (*.h5)", "*.h5"),
                ("HDF5 files (*.hdf5)", "*.hdf5"),
                ("All files", "*.*"),
            ],
            title="Load Session",
        )
        if not file_path:
            return

        try:
            view_state = self.model.load_session(file_path)

            if "show_groups" in view_state:
                self.view.show_groups.set(bool(view_state["show_groups"]))
            if "show_histograms" in view_state:
                self.view.show_histograms.set(bool(view_state["show_histograms"]))
            if "show_inputs" in view_state:
                self.view.show_inputs.set(bool(view_state["show_inputs"]))
            if "show_outputs" in view_state:
                self.view.show_outputs.set(bool(view_state["show_outputs"]))
            if "view_mode" in view_state:
                self.view.view_mode.set(str(view_state["view_mode"]))
            if "sort_key" in view_state:
                self.view.sort_key.set(str(view_state["sort_key"]))
            if "sort_desc" in view_state:
                self.view.sort_desc.set(bool(view_state["sort_desc"]))

            messagebox.showinfo("Session Loaded", f"Session loaded from:\n{file_path}")
        except Exception:
            logger.exception("Failed to load session")
            messagebox.showerror(
                "Session Load Failed",
                "Could not load session. Please verify the file and try again.",
            )

    def import_filelist(self) -> None:
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
    
    def import_settings(self, file_path: str | None = None) -> None:
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

    def import_default_settings(self) -> None:
        """Import default settings from user config location, with legacy fallback."""
        if os.path.exists(self.default_settings_path):
            self.import_settings(self.default_settings_path)
            return

        legacy_path = "msa_options.json"
        if os.path.exists(legacy_path):
            self.import_settings(legacy_path)

    def toggle_checkbox(self, checkbox: tk.BooleanVar) -> None:
        # Toggle a Tkinter BooleanVar checkbox
        if checkbox.get():
            checkbox.set(False)
        else:
            checkbox.set(True)
        return

    def _build_settings_dict(self) -> dict[str, Any]:
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

    def export_settings(self) -> None:
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

    def export_default_settings(self) -> None:
        """Save current settings as the default in the per-user config location."""
        parent_dir = os.path.dirname(self.default_settings_path)
        os.makedirs(parent_dir, exist_ok=True)
        with open(self.default_settings_path, "w", encoding="utf-8") as f:
            json.dump(self._build_settings_dict(), f, indent=2)
        messagebox.showinfo("Default Settings", f"Settings saved as default:\n{self.default_settings_path}")

    def export_logs(self) -> None:
        """Export current logs and metadata as a ZIP bundle for bug reporting."""
        default_name = f"msa_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        destination = asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")],
            title="Export Logs As",
            initialfile=default_name,
        )
        if not destination:
            return

        try:
            saved_path = export_logs_bundle(destination)
            messagebox.showinfo(
                "Logs Exported",
                f"A diagnostic log bundle was saved to:\n{saved_path}\n\nPlease attach this ZIP file to your bug report.",
            )
            logger.info("Exported log bundle to %s", saved_path)
        except Exception:
            logger.exception("Failed to export log bundle")
            messagebox.showerror(
                "Export Failed",
                "Could not export logs. Please try a different location and try again.",
            )