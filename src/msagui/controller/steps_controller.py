import csv
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from msagui.view.steps_view import MultiCorrectionsDialog

_STEP_FIELDS = ["keyword1", "operation", "keyword2", "value", "output_key"]

class StepsController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.dialog = None
        
    def open(self):
        print("Opening steps dialog...")
        """Open dialog to input multiple corrections and factors."""
        if self.dialog is not None:
            try:
                if self.dialog.winfo_exists():
                    self.dialog.lift()
                    self.dialog.focus_force()
                    return
            except Exception:
                self.dialog = None

        self.dialog = MultiCorrectionsDialog(self.view.root, self.model.get_steps())
        self.dialog.bind("<Destroy>", self._on_dialog_destroyed)
        self.dialog.save_button.config(command=self.close)
        self.dialog.import_button.config(command=self.import_steps)
        self.dialog.export_button.config(command=self.export_steps)

    def _on_dialog_destroyed(self, _event=None):
        if self.dialog is None:
            return
        if _event is not None and _event.widget is not self.dialog:
            return
        self.dialog = None

    def _parse_steps_csv(self, reader: csv.DictReader) -> list[dict[str, str]]:
        """Validate and parse step rows from a DictReader."""
        header = reader.fieldnames or []
        if header != _STEP_FIELDS:
            expected = ", ".join(_STEP_FIELDS)
            found_full = ", ".join(header) if header else "<missing header>"
            found = (found_full[:50] + "...") if len(found_full) > 50 else found_full
            raise ValueError(
                "Invalid step file format.\n\n"
                f"Expected header:\n{expected}\n\n"
                f"Found:\n{found}"
            )

        steps = []
        for row_idx, row in enumerate(reader, start=2):
            if any(k not in row for k in _STEP_FIELDS):
                raise ValueError(f"Invalid row format at line {row_idx}.")
            cleaned = {k: (row.get(k, "") or "").strip() for k in _STEP_FIELDS}
            steps.append(cleaned)
        return steps

    def import_steps(self):
        """Load steps from a CSV file and populate the dialog view."""
        if self.dialog is None:
            return
        dialog = self.dialog

        file_path = filedialog.askopenfilename(
            parent=dialog,
            title="Import Steps",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file_path:
            return
        try:
            with open(file_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                steps = self._parse_steps_csv(reader)
        except ValueError as e:
            messagebox.showerror("Import Error", str(e), parent=dialog)
            return
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to read file:\n{e}", parent=dialog)
            return
        dialog.load_step_data(steps)

    def export_steps(self):
        """Write the current dialog step entries to a CSV file."""
        if self.dialog is None:
            return
        dialog = self.dialog

        file_path = filedialog.asksaveasfilename(
            parent=dialog,
            title="Export Steps",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file_path:
            return
        steps = dialog.get_step_data()
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=_STEP_FIELDS)
                writer.writeheader()
                writer.writerows(steps)
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to write file:\n{e}", parent=dialog)
        
    def close(self):
        print("[Close] Saving steps and closing dialog...")
        """Collect all steps and close dialog."""
        if self.dialog is None:
            return

        steps = []
        for row in self.dialog.step_rows:
            _, keyword, operation, keyword2, value, output_key, _, _, _ = row
            step = {
                "keyword1": keyword.get().strip(),
                "operation": operation.get().strip(),
                "keyword2": keyword2.get().strip(),
                "value": value.get().strip(),
                "output_key": output_key.get().strip()
            }
            if step["keyword1"] and step["operation"] and step["output_key"]:
                steps.append(step)
        self.dialog.destroy()
        print("Collected steps:", steps)
        self.model.steps.set_steps(steps)