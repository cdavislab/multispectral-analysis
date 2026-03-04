import tkinter as tk
class MultiCorrectionsDialog(tk.Toplevel):
    """Dialog for entering multiple correction steps with operations and output keys."""
    def __init__(self, parent, steps):
        super().__init__(parent)
        self.title("Analysis Set-Up")
        self.geometry("1000x600")
        self.steps = steps
        self.result = None

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
        self.op_buttons = []
        ops = [("A + B", "+"), ("A * B", "*"), ("A - B", "-"), ("A / B", "/")]
        for i, (label, op) in enumerate(ops):
            btn = tk.Button(self.op_frame, text=label, width=10, command=lambda o=op: self.open_op_dialog(o))
            btn.grid(row=i//2, column=i%2, padx=5, pady=5)
            self.op_buttons.append(btn)

        # Threshold button
        self.threshold_button = tk.Button(self.right_pane, text="Threshold", width=22, command=self.open_threshold_dialog)
        self.threshold_button.pack(pady=(30, 10))

        # Save button
        self.save_button = tk.Button(self.right_pane, text="Save", width=22)
        self.save_button.pack(pady=(10, 0))

    def add_step_row(self, step=None):
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

    def move_step_row(self, idx, direction):
        """Move a step row up or down in the list, preventing out-of-bounds moves and refreshing entry text."""
        new_idx = idx + direction
        if 0 <= new_idx < len(self.step_rows):
            # Swap the data in the step_rows list
            self.step_rows[idx], self.step_rows[new_idx] = self.step_rows[new_idx], self.step_rows[idx]
            self.update_row_numbers()
            self.refresh_entry_texts()

    def delete_step_row(self, idx):
        """Delete a step row from the table."""
        row = self.step_rows.pop(idx)
        # Destroy all widgets in the row
        for widget in row:
            if widget is not None:
                widget.destroy()
        self.update_row_numbers()

    def update_row_numbers(self):
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

    def refresh_entry_texts(self):
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

    def open_op_dialog(self, op):
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

    def open_threshold_dialog(self):
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
        def __init__(self, parent, op):
            super().__init__(parent)
            self.title(f"Operation: {op}")
            self.result = None
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

        def on_ok(self):
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
        def __init__(self, parent):
            super().__init__(parent)
            self.title("Threshold")
            self.result = None
            tk.Label(self, text="Keyword:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            self.keyword = tk.Entry(self)
            self.keyword.grid(row=0, column=1, padx=5, pady=5)
            tk.Label(self, text="Threshold value:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
            self.threshold = tk.Entry(self)
            self.threshold.grid(row=1, column=1, padx=5, pady=5)
            tk.Label(self, text="Output key:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
            self.output_key = tk.Entry(self)
            self.output_key.grid(row=2, column=1, padx=5, pady=5)
            tk.Button(self, text="OK", command=self.on_ok).grid(row=3, column=0, columnspan=2, pady=10)

        def on_ok(self):
            self.result = {
                "keyword1": self.keyword.get().strip(),
                "threshold": self.threshold.get().strip(),
                "output_key": self.output_key.get().strip()
            }
            self.destroy()