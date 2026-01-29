import tkinter as tk

class ProgressBar(tk.Toplevel):
    """Simple progress bar dialog."""
    def __init__(self, title="Progress Bar"):
        super().__init__()
        self.title(title)
        self.geometry("400x150")
        self.canvas = tk.Canvas(self, width=300, height=30, bg='white', highlightthickness=1, highlightbackground='black')
        self.canvas.pack(pady=40)
        self.progress = 0
        self.canvas.delete("progress")
        self.update_progress(0)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.destroy()
    def update_progress(self, value: float):
        """Update the progress bar on the canvas."""
        self.canvas.delete("progress")
        fill_width = (value / 100) * 300
        self.canvas.create_rectangle(0, 0, fill_width, 30, fill="green", tags="progress")
        self.update()

def open_multi_corrections_dialog(self):
    """Open dialog to input multiple corrections and factors."""
    dialog = self.MultiCorrectionsDialog(self.root)#, self.steps)
    if dialog.result is not None:
        # Store results for controller/model access
        self.multiple_corrections = dialog.result['corrections']
        self.multiple_factors = dialog.result['factors']