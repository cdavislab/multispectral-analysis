import csv
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from msagui.view.steps_view import MultiCorrectionsDialog

_STEP_FIELDS = ["keyword1", "operation", "keyword2", "value", "output_key"]

class StepsController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        
    def open(self):
        print("Opening steps dialog...")
        """Open dialog to input multiple corrections and factors."""
        self.dialog = MultiCorrectionsDialog(self.view.root, self.model.get_steps())
        self.dialog.save_button.config(command=self.close)
        self.dialog.import_button.config(command=self.import_steps)
        self.dialog.export_button.config(command=self.export_steps)

    def import_steps(self):
        """Load steps from a CSV file and populate the dialog view."""
        file_path = filedialog.askopenfilename(
            parent=self.dialog,
            title="Import Steps",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file_path:
            return
        try:
            with open(file_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                steps = [row for row in reader]
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to read file:\n{e}", parent=self.dialog)
            return
        self.dialog.load_step_data(steps)

    def export_steps(self):
        """Write the current dialog step entries to a CSV file."""
        file_path = filedialog.asksaveasfilename(
            parent=self.dialog,
            title="Export Steps",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file_path:
            return
        steps = self.dialog.get_step_data()
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=_STEP_FIELDS)
                writer.writeheader()
                writer.writerows(steps)
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to write file:\n{e}", parent=self.dialog)
        
    def close(self):
        print("[Close] Saving steps and closing dialog...")
        """Collect all steps and close dialog."""
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