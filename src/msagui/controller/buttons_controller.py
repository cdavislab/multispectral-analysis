
from tkinter.filedialog import askopenfilenames, askdirectory
import tkinter as tk
import tkinter.messagebox as messagebox
import os
from msagui.view.progress_bar import ProgressBar

class ButtonsController:
    def __init__(self, model, view):
        self.model = model
        self.view = view

    def add(self):
        files = askopenfilenames(
            filetypes=(("Comma Delimited", "*.csv"), ("All files", "*.*"))
        )
        if not files:
            return

        with ProgressBar(title="Processing", total=len(files)) as progress:
            results = self.model.add(files, progress_callback=progress.step)

        if len(results.keys()) != 0:
            self.view.show_error(results)
        
    def delete(self):
        # Delete selected files from listbox and model
        idx_to_del = self.view.listbox.get_selected_indices()
        if not idx_to_del:
            return

        with ProgressBar(title="Deleting Files", total=len(idx_to_del)) as progress:
            results = self.model.delete(idx_to_del, progress_callback=progress.step)

        if len(results.keys()) != 0:
            self.view.show_error(results)


    #TODO: Troubleshoot addition of dictionaries and swap to freq1 vs lw
    def validate_entries(self):
        # Validate user input fields before analysis
        # Ignore analyze request if no files are loaded
        if self.model.df.empty:
            messagebox.showerror("Add Files", "Add files using \"Add Files\" button before analyzing.")
            return None
        if self.view.show_groups.get():
            messagebox.showerror("Group View", "Cannot analyze in group view.")
            return None
        if not self.view.show_inputs.get():
            messagebox.showerror("Inputs Hidden", "Please show inputs before analyzing.")
            return None
        # Get the values from the entries
        entry_keys = ('freq1', 'freq2', 'freq1c', 'freq2c', 'threshold', 'freq1cf', 'freq2cf')
        args = self.view.get_settings()
        args = {key: args[key] for key in entry_keys}
        # Check if required fields are empty
        if any(args[key] == '' for key in ['freq1', 'freq2']):
            messagebox.showerror("Missing Fields", "Please fill out all fields before analyzing.")
            return None
        # Convert the string inputs to floats
        for key in ['threshold','freq1cf', 'freq2cf']:
            s = args[key]
            try:
                args[key] = float(s) if s.strip() else 0.0
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter an integer or decimal for the number of wavenumbers.")
                return None
            
        
        # If the correction factor is non-zero, but no correction factor label is entered, show an error
        if ('' == args['freq1c']) and (args['freq1cf'] != 0):
            messagebox.showerror("Missing Fields", "Please enter a label for Frequency 1 Correction.")
            return None
        if ('' == args['freq2c']) and (args['freq2cf'] != 0):
            messagebox.showerror("Missing Fields", "Please enter a label for Frequency 2 Correction.")
            return None
        # If the correction factor for frequency is 0, set correction factor label to None
        if args['freq1cf'] == 0:
            args['freq1c'] = None
        if args['freq2cf'] == 0:
            args['freq2c'] = None
        # If the view has multiple corrections/factors, add them to args
        if hasattr(self.view, 'multiple_corrections') and hasattr(self.view, 'multiple_factors'):
            args['multiple_corrections'] = self.view.multiple_corrections
            args['multiple_factors'] = self.view.multiple_factors
        return args

    def count_unique_types(self, entries):
        # Count unique types among frequency/correction entries
        types = set([entries['freq1'],
                 entries['freq2'],
                 entries['freq1c'],
                 entries['freq2c']])
        if None in types:
            types.remove(None)
        return len(types)

    def group(self):
        self.model.set_keywords()
        self.model.set_groups()

    def analyze(self):
        selected_idx = self.view.listbox.get_selected_indices()
        if not selected_idx:
            messagebox.showerror("No Selection", "Please select at least one file to analyze.")
            return
        with ProgressBar(title="Analyzing", total=len(selected_idx)) as progress:
            error = self.model.analyze(selected_idx, progress_callback=progress)
            messagebox.showerror("Analysis Error", error) if error else None

    def _ask_export_scope(self) -> dict | None:
        """Show a dialog asking whether to export all or selected images,
        with an optional checkbox to also export statistics.

        Returns a dict ``{"scope": "all"|"selected", "export_stats": bool}``,
        or ``None`` if the user cancels.
        """
        import tkinter as tk

        result = [None]

        win = tk.Toplevel()
        win.title("Export Images")
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="Which images would you like to export?",
                 padx=20, pady=12).pack()

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=(0, 6))

        def choose(value):
            result[0] = value
            win.destroy()

        tk.Button(btn_frame, text="All Images", width=14,
                  command=lambda: choose("all")).grid(row=0, column=0, padx=6)
        tk.Button(btn_frame, text="Selected Only", width=14,
                  command=lambda: choose("selected")).grid(row=0, column=1, padx=6)
        tk.Button(btn_frame, text="Cancel", width=10,
                  command=lambda: choose(None)).grid(row=0, column=2, padx=6)

        stats_var = tk.BooleanVar(value=False)
        chk_frame = tk.Frame(win)
        chk_frame.pack(pady=(0, 10))
        tk.Checkbutton(chk_frame, text="Export Statistics", variable=stats_var).pack()

        win.wait_window()
        if result[0] is None:
            return None
        return {"scope": result[0], "export_stats": stats_var.get()}

    def export_images(self):
        """Prompt for a folder and save every visible image into it."""
        choice = self._ask_export_scope()
        if choice is None:
            return
        scope = choice["scope"]
        do_export_stats = choice["export_stats"]

        # Build the candidate list from all visible items.
        all_visible = [
            (idx, meta)
            for idx, meta in enumerate(self.model.metadata.items)
            if meta.visible
        ]

        if scope == "selected":
            selected_lb = self.view.listbox.get_selected_indices()
            if not selected_lb:
                messagebox.showerror("Export", "No images are selected. "
                                     "Please select images in the list first.")
                return
            # Listbox positions map 1-to-1 onto all_visible.
            items = [all_visible[i] for i in selected_lb if i < len(all_visible)]
        else:
            items = all_visible

        if not items:
            messagebox.showinfo("Export", "No images to export.")
            return

        directory = askdirectory(title="Choose Export Folder")
        if not directory:
            return

        ext = self.model.settings.export_format.lstrip(".")
        ext = "." + ext

        errors = {}
        with ProgressBar(title="Exporting Images", total=len(items)) as progress:
            for idx, meta in items:
                try:
                    image, _stats = self.model.make_image(idx)
                    # JPEG/BMP don't support alpha — convert to RGB when needed.
                    if ext.lower() in (".jpg", ".jpeg", ".bmp") and image.mode in ("RGBA", "LA", "P"):
                        image = image.convert("RGB")
                    parent_folder = os.path.basename(os.path.dirname(meta.nickname))
                    stem = os.path.splitext(os.path.basename(meta.nickname))[0]
                    if parent_folder:
                        subfolder = os.path.join(directory, parent_folder)
                        os.makedirs(subfolder, exist_ok=True)
                    else:
                        subfolder = directory
                    out_path = os.path.join(subfolder, stem + ext)
                    image.save(out_path)
                except Exception as e:
                    errors[meta.nickname] = e
                finally:
                    progress.step()

        if errors:
            self.view.show_error(errors)
        else:
            messagebox.showinfo("Export", f"Exported {len(items)} image(s) to:\n{directory}")
        if do_export_stats:
            self.model.export_stats(directory=directory)