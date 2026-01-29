import tkinter as tk

class ProgressBar(tk.Toplevel):
    """Simple progress bar dialog."""
    def __init__(self, title="Progress Bar", total=100):
        super().__init__()
        self.title(title)
        self.geometry("400x150")
        self.canvas = tk.Canvas(self, width=300, height=30, bg='white', highlightthickness=1, highlightbackground='black')
        self.canvas.pack(pady=40)
        self.progress = 1
        self.step_size = self.get_step_size(total)
        self.canvas.delete("progress")

    def draw_progress(self):
        """Draw the initial empty progress bar."""
        self.canvas.delete("progress")
        fill_width = (self.progress / 100) * 300
        self.canvas.create_rectangle(0, 0, fill_width, 30, fill="green", tags="progress")
        self.update()

    def step(self):
        """Increment the progress bar by one step."""
        
        self.progress += self.step_size
        self.progress = min(100, self.progress)

    def get_step_size(self, total):
        """Calculate the step size for progress updates."""
        return 100 / total
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.destroy()
        

def open_multi_corrections_dialog(self):
    """Open dialog to input multiple corrections and factors."""
    dialog = self.MultiCorrectionsDialog(self.root)#, self.steps)
    if dialog.result is not None:
        # Store results for controller/model access
        self.multiple_corrections = dialog.result['corrections']
        self.multiple_factors = dialog.result['factors']