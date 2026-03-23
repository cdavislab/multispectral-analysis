import tkinter as tk
from tkinter import ttk
from typing import Any


class MultiCorrectionsDialog(tk.Toplevel):
    """Dialog for entering multiple correction steps with operations and output keys."""
    def __init__(self, parent: tk.Widget, steps: list[dict[str, str]]) -> None:
        super().__init__(parent)
        self.title("Analysis Set-Up")
        self.transient(parent)
        self.geometry("1050x400")
        self.minsize(1050, 400)
        self._position_window(parent, width=1050, height=400)
        self.steps = steps
        self.result: dict[str, str] | None = None

        # Main frame with two panes
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left pane: steps table
        self.left_pane = tk.Frame(self.main_frame)
        self.left_pane.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Right pane: operation buttons
        self.right_pane = tk.Frame(self.main_frame)
        self.right_pane.pack(side=tk.RIGHT, fill=tk.Y)

        # Table headers
        headers = ["#", "keyword1", "operation", "keyword2", "value", "output key", "", ""]
        for col, header in enumerate(headers):
            tk.Label(self.left_pane, text=header, font=("Verdana", 9, "bold")).grid(row=0, column=col, padx=2, pady=2)

        self.step_rows = []
        self.next_row = 1

        # Populate with existing steps
        if self.steps:
            for step in self.steps:
                self.add_step_row(step)
        else:
            self.add_step_row()  # Optionally start with one empty row if no steps

        # Add step button at the bottom of left pane
        self.add_step_button = tk.Button(self.left_pane, text="Add step", command=self.add_step_row)
        self.add_step_button.grid(row=1000, column=0, columnspan=8, sticky="ew", pady=(10,0))

        # Right pane: operation buttons (2x2 grid)
        self.op_frame = tk.Frame(self.right_pane)
        self.op_frame.pack(pady=10)
        self.op_frame.grid_columnconfigure(0, weight=1)
        self.op_frame.grid_columnconfigure(1, weight=1)
        self.op_buttons = []
        ops = [("A + B", "+"), ("A * B", "*"), ("A - B", "-"), ("A / B", "/")]
        for i, (label, op) in enumerate(ops):
            btn = tk.Button(self.op_frame, text=label, width=10, command=lambda o=op: self.open_op_dialog(o))
            btn.grid(row=i//2, column=i%2, sticky="ew", padx=2, pady=2)
            self.op_buttons.append(btn)

        # Threshold button
        self.threshold_button = tk.Button(self.op_frame, text="Threshold", command=self.open_threshold_dialog)
        self.threshold_button.grid(row=2, column=0, columnspan=2, sticky="ew", padx=2, pady=2)

        # Visual divider between operation controls and file/save controls
        self.controls_separator = ttk.Separator(self.op_frame, orient="horizontal")
        self.controls_separator.grid(row=3, column=0, columnspan=2, sticky="ew", padx=2, pady=(10, 10))

        # Save button
        self.save_button = tk.Button(self.op_frame, text="Save")
        self.save_button.grid(row=4, column=0, columnspan=2, sticky="ew", padx=2, pady=(0, 8))

        # Import/Export buttons
        self.import_button = tk.Button(self.op_frame, text="Import Steps")
        self.import_button.grid(row=5, column=0, sticky="ew", padx=2, pady=(0, 2))
        self.export_button = tk.Button(self.op_frame, text="Export Steps")
        self.export_button.grid(row=5, column=1, sticky="ew", padx=2, pady=(0, 2))

    def _position_window(self, parent: tk.Widget, width: int, height: int) -> None:
        """Center dialog over parent and keep it fully on-screen."""
        self.update_idletasks()

        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()

        x = px + max(0, (pw - width) // 2)
        y = py + max(0, (ph - height) // 2)

        x = max(0, min(x, sw - width))
        y = max(0, min(y, sh - height))

        self.geometry(f"{width}x{height}+{x}+{y}")

    def add_step_row(self, step: dict[str, str] | None = None) -> None:
        """Add a row to the steps table. Optionally populate with a step dict."""
        row = self.next_row
        self.next_row += 1
        step_num = tk.Label(self.left_pane, text=str(row))
        keyword = tk.Entry(self.left_pane, width=12)
        operation = tk.Entry(self.left_pane, width=6)
        keyword2 = tk.Entry(self.left_pane, width=12)
        value = tk.Entry(self.left_pane, width=8)
        output_key = tk.Entry(self.left_pane, width=12)
        # Placeholders for up/down/delete buttons, will be created in update_row_numbers
        up_btn = None
        down_btn = None
        del_btn = None
        widgets = [step_num, keyword, operation, keyword2, value, output_key, up_btn, down_btn, del_btn]
        if step:
            keyword.insert(0, step.get("keyword1", ""))
            operation.insert(0, step.get("operation", ""))
            keyword2.insert(0, step.get("keyword2", ""))
            value.insert(0, step.get("value", ""))
            output_key.insert(0, step.get("output_key", ""))
        self.step_rows.append([step_num, keyword, operation, keyword2, value, output_key, up_btn, down_btn, del_btn])
        self.update_row_numbers()

    def move_step_row(self, idx: int, direction: int) -> None:
        """Move a step row up or down in the list, preventing out-of-bounds moves and refreshing entry text."""
        new_idx = idx + direction
        if 0 <= new_idx < len(self.step_rows):
            # Swap the data in the step_rows list
            self.step_rows[idx], self.step_rows[new_idx] = self.step_rows[new_idx], self.step_rows[idx]
            self.update_row_numbers()
            self.refresh_entry_texts()

    def delete_step_row(self, idx: int) -> None:
        """Delete a step row from the table."""
        row = self.step_rows.pop(idx)
        # Destroy all widgets in the row
        for widget in row:
            if widget is not None:
                widget.destroy()
        self.update_row_numbers()

    def update_row_numbers(self) -> None:
        """Update the row numbers, re-grid widgets, and create unique up/down/delete buttons for each row."""
        for idx, row in enumerate(self.step_rows, start=1):
            row[0].config(text=str(idx))
            # Remove old up/down/delete buttons if they exist
            if row[6]:
                row[6].destroy()
            if row[7]:
                row[7].destroy()
            if row[8]:
                row[8].destroy()
            # Create new up/down/delete buttons with correct index
            up_btn = tk.Button(self.left_pane, text="↑", width=2, command=lambda idx=idx-1: self.move_step_row(idx, -1))
            down_btn = tk.Button(self.left_pane, text="↓", width=2, command=lambda idx=idx-1: self.move_step_row(idx, 1))
            del_btn = tk.Button(self.left_pane, text="X", width=2, fg="red", command=lambda idx=idx-1: self.delete_step_row(idx))
            row[6] = up_btn
            row[7] = down_btn
            row[8] = del_btn
            for col, widget in enumerate(row):
                widget.grid(row=idx, column=col, padx=2, pady=2)
            # Disable up button for first row, down button for last row
            if idx == 1:
                up_btn.config(state=tk.DISABLED)
            else:
                up_btn.config(state=tk.NORMAL)
            if idx == len(self.step_rows):
                down_btn.config(state=tk.DISABLED)
            else:
                down_btn.config(state=tk.NORMAL)

    def refresh_entry_texts(self) -> None:
        """Refresh the text in the entries to reflect the new order in step_rows."""
        # Extract all entry values in order
        entry_values = []
        for row in self.step_rows:
            entry_values.append([
                row[1].get(),  # keyword
                row[2].get(),  # operation
                row[3].get(),  # keyword2
                row[4].get(),  # value
                row[5].get(),  # output_key
            ])
        # After reordering, set the text in each entry to match the new order
        for row, values in zip(self.step_rows, entry_values):
            row[1].delete(0, tk.END)
            row[1].insert(0, values[0])
            row[2].delete(0, tk.END)
            row[2].insert(0, values[1])
            row[3].delete(0, tk.END)
            row[3].insert(0, values[2])
            row[4].delete(0, tk.END)
            row[4].insert(0, values[3])
            row[5].delete(0, tk.END)
            row[5].insert(0, values[4])

    def get_step_data(self) -> list[dict[str, str]]:
        """Return the current entry widget values as a list of step dicts."""
        return [
            {
                "keyword1":   row[1].get().strip(),
                "operation":  row[2].get().strip(),
                "keyword2":   row[3].get().strip(),
                "value":      row[4].get().strip(),
                "output_key": row[5].get().strip(),
            }
            for row in self.step_rows
        ]

    def load_step_data(self, steps: list[dict[str, str]]) -> None:
        """Clear all current rows and repopulate the table from a list of step dicts."""
        for row in list(self.step_rows):
            for widget in row:
                if widget is not None:
                    widget.destroy()
        self.step_rows.clear()
        self.next_row = 1
        for step in steps:
            self.add_step_row(step)

    def open_op_dialog(self, op: str) -> None:
        """Open dialog for arithmetic operation step."""
        dialog = self.OperationDialog(self, op)
        self.wait_window(dialog)
        if dialog.result:
            # Add a new step row with dialog result
            step = {
                "keyword1": dialog.result["keyword1"],
                "operation": op,
                "keyword2": dialog.result["keyword2"] if dialog.result["mode"] == "image" else "",
                "value": dialog.result["value"] if dialog.result["mode"] == "constant" else "",
                "output_key": dialog.result["output_key"]
            }
            self.add_step_row(step)

    def open_threshold_dialog(self) -> None:
        """Open dialog for threshold operation step."""
        dialog = self.ThresholdDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            step = {
                "keyword1": dialog.result["keyword1"],
                "operation": "threshold",
                "keyword2": "",
                "value": dialog.result["threshold"],
                "output_key": dialog.result["output_key"]
            }
            self.add_step_row(step)

    class OperationDialog(tk.Toplevel):
        """Dialog for arithmetic operation step."""
        def __init__(self, parent: tk.Widget, op: str) -> None:
            super().__init__(parent)
            self.title(f"Operation: {op}")
            self.result: dict[str, str] | None = None
            tk.Label(self, text="Keyword (A):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            self.keyword1 = tk.Entry(self)
            self.keyword1.grid(row=0, column=1, padx=5, pady=5)
            tk.Label(self, text=f"Operation: {op}").grid(row=1, column=0, columnspan=2, pady=5)
            tk.Label(self, text="Keyword/Value (B):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
            self.keyword2 = tk.Entry(self)
            self.keyword2.grid(row=2, column=1, padx=5, pady=5)
            self.mode = tk.StringVar(value="image")
            tk.Radiobutton(self, text="image", variable=self.mode, value="image").grid(row=3, column=0, padx=5, pady=2)
            tk.Radiobutton(self, text="constant", variable=self.mode, value="constant").grid(row=3, column=1, padx=5, pady=2)
            tk.Label(self, text="Output key:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
            self.output_key = tk.Entry(self)
            self.output_key.grid(row=4, column=1, padx=5, pady=5)
            tk.Button(self, text="OK", command=self.on_ok).grid(row=5, column=0, columnspan=2, pady=10)

        def on_ok(self) -> None:
            self.result = {
                "keyword1": self.keyword1.get().strip(),
                "keyword2": self.keyword2.get().strip(),
                "mode": self.mode.get(),
                "value": self.keyword2.get().strip() if self.mode.get() == "constant" else "",
                "output_key": self.output_key.get().strip()
            }
            self.destroy()

    class ThresholdDialog(tk.Toplevel):
        """Dialog for threshold operation step."""
        def __init__(self, parent: tk.Widget) -> None:
            super().__init__(parent)
            self.title("Threshold")
            self.result: dict[str, str] | None = None
            tk.Label(self, text="Keyword:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            self.keyword = tk.Entry(self)
            self.keyword.grid(row=0, column=1, padx=5, pady=5)

            tk.Label(self, text="Threshold proportion:").grid(row=1, column=0, padx=5, pady=(5,0), sticky="e")
            self.threshold = tk.Entry(self)
            self.threshold.grid(row=1, column=1, padx=5, pady=5)
            
            hint = "Proportion of max value in image (e.g. 0.10)"
            tk.Label(self, text=hint, fg='gray').grid(row=2, column=0, columnspan=2, padx=5, pady=(0,5), sticky="w")

            tk.Label(self, text="Output key:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
            self.output_key = tk.Entry(self)
            self.output_key.grid(row=3, column=1, padx=5, pady=5)
            tk.Button(self, text="OK", command=self.on_ok).grid(row=4, column=0, columnspan=2, pady=10)

        def on_ok(self) -> None:
            self.result = {
                "keyword1": self.keyword.get().strip(),
                "threshold": self.threshold.get().strip(),
                "output_key": self.output_key.get().strip()
            }
            self.destroy()