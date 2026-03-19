
from tkinter.filedialog import askopenfilenames, askdirectory
import tkinter as tk
import tkinter.messagebox as messagebox
import os
import logging
from msagui.view.progress_bar import ProgressBar

logger = logging.getLogger(__name__)

class ButtonsController:
    def __init__(self, model, view, listbox_ctrl=None):
        self.model = model
        self.view = view
        self.listbox_ctrl = listbox_ctrl

    def add(self):
        files = askopenfilenames(
            filetypes=(("Comma Delimited", "*.csv"), ("All files", "*.*"))
        )
        if not files:
            logger.debug("Add canceled by user")
            return

        logger.info("Adding %d file(s)", len(files))
        with ProgressBar(title="Processing", total=len(files)) as progress:
            results = self.model.add(files, progress_callback=progress.step)

        if len(results.keys()) != 0:
            logger.warning("Add completed with %d failure(s)", len(results))
            self.view.show_error(results)
        
    def delete(self):
        # Delete selected files from listbox and model
        if self.listbox_ctrl is not None:
            idx_to_del = self.listbox_ctrl.get_selected_metadata_indices()
        else:
            idx_to_del = self.view.listbox.get_selected_indices()
        if not idx_to_del:
            logger.debug("Delete requested with no selected items")
            return

        logger.info("Deleting %d selected item(s)", len(idx_to_del))
        with ProgressBar(title="Deleting Files", total=len(idx_to_del)) as progress:
            results = self.model.delete(idx_to_del, progress_callback=progress.step)

        if len(results.keys()) != 0:
            logger.warning("Delete completed with %d failure(s)", len(results))
            self.view.show_error(results)


    #TODO: Troubleshoot addition of dictionaries and swap to freq1 vs lw
    def validate_entries(self):
        # Validate user input fields before analysis
        # Ignore analyze request if no files are loaded
        if self.model.df.empty:
            logger.warning("Analyze blocked: no files loaded")
            messagebox.showerror("Add Files", "Add files using \"Add Files\" button before analyzing.")
            return None
        if self.view.show_groups.get():
            logger.warning("Analyze blocked: attempted in group view")
            messagebox.showerror("Group View", "Cannot analyze in group view.")
            return None
        if not self.view.show_inputs.get():
            logger.warning("Analyze blocked: inputs are hidden")
            messagebox.showerror("Inputs Hidden", "Please show inputs before analyzing.")
            return None
        # Get the values from the entries
        entry_keys = ('freq1', 'freq2', 'freq1c', 'freq2c', 'threshold', 'freq1cf', 'freq2cf')
        args = self.view.get_settings()
        args = {key: args[key] for key in entry_keys}
        # Check if required fields are empty
        if any(args[key] == '' for key in ['freq1', 'freq2']):
            logger.warning("Analyze blocked: missing required frequency fields")
            messagebox.showerror("Missing Fields", "Please fill out all fields before analyzing.")
            return None
        # Convert the string inputs to floats
        for key in ['threshold','freq1cf', 'freq2cf']:
            s = args[key]
            try:
                args[key] = float(s) if s.strip() else 0.0
            except ValueError:
                logger.warning("Analyze blocked: invalid numeric value for %s: %r", key, s)
                messagebox.showerror("Invalid Input", "Please enter an integer or decimal for the number of wavenumbers.")
                return None
            
        
        # If the correction factor is non-zero, but no correction factor label is entered, show an error
        if ('' == args['freq1c']) and (args['freq1cf'] != 0):
            logger.warning("Analyze blocked: freq1 correction factor provided without freq1c label")
            messagebox.showerror("Missing Fields", "Please enter a label for Frequency 1 Correction.")
            return None
        if ('' == args['freq2c']) and (args['freq2cf'] != 0):
            logger.warning("Analyze blocked: freq2 correction factor provided without freq2c label")
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
        if self.listbox_ctrl is not None:
            selected_idx = self.listbox_ctrl.get_selected_metadata_indices()
        else:
            selected_idx = self.view.listbox.get_selected_indices()
        if not selected_idx:
            logger.warning("Analyze requested with no selection")
            messagebox.showerror("No Selection", "Please select at least one file to analyze.")
            return
        logger.info("Starting analyze for %d selected item(s)", len(selected_idx))
        with ProgressBar(title="Analyzing", total=len(selected_idx)) as progress:
            error = self.model.analyze(selected_idx, progress_callback=progress)
            if error:
                logger.error("Analyze failed: %s", error)
                messagebox.showerror("Analysis Error", error)
            else:
                logger.info("Analyze completed successfully")

    def _ask_export_scope(self) -> dict | None:
        """Show a dialog asking whether to export all or selected images,
        with optional export toggles.

        Returns a dict with ``scope`` and toggle states,
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
        is_group_view = hasattr(self.view, "show_groups") and self.view.show_groups.get()
        groups_var = tk.BooleanVar(value=is_group_view)
        histogram_var = tk.BooleanVar(value=False)
        subdivide_var = tk.BooleanVar(value=True)

        chk_frame = tk.Frame(win)
        chk_frame.pack(pady=(0, 10))
        chk_frame.grid_columnconfigure(0, weight=1, uniform="export_opts")
        chk_frame.grid_columnconfigure(1, weight=1, uniform="export_opts")
        groups_chk = tk.Checkbutton(chk_frame, text="Groups", variable=groups_var)
        groups_chk.grid(row=0, column=0, padx=10, sticky="w")
        if is_group_view:
            groups_chk.configure(state="disabled")
        tk.Checkbutton(chk_frame, text="Histogram", variable=histogram_var).grid(row=0, column=1, padx=10, sticky="w")
        tk.Checkbutton(chk_frame, text="Export Statistics", variable=stats_var).grid(row=1, column=0, padx=10, sticky="w")
        tk.Checkbutton(chk_frame, text="Subdivide", variable=subdivide_var).grid(row=1, column=1, padx=10, sticky="w")

        win.wait_window()
        if result[0] is None:
            return None
        return {
            "scope": result[0],
            "export_stats": stats_var.get(),
            "groups": groups_var.get(),
            "histogram": histogram_var.get(),
            "subdivide": subdivide_var.get(),
        }

    def export_images(self):
        """Prompt for a folder and save every visible image into it."""
        choice = self._ask_export_scope()
        if choice is None:
            logger.debug("Export canceled at scope selection")
            return
        scope = choice["scope"]
        do_export_stats = choice["export_stats"]
        do_export_groups = choice["groups"]
        do_export_histograms = choice["histogram"]
        do_subdivide = choice["subdivide"]
        is_group_view = hasattr(self.view, "show_groups") and self.view.show_groups.get()

        # Build the candidate list from all visible items.
        all_visible = [
            (idx, meta)
            for idx, meta in enumerate(self.model.metadata.items)
            if meta.visible
        ]

        selected_group_ids = []
        selected_meta_idx = []
        if scope == "selected":
            if is_group_view and self.listbox_ctrl is not None:
                selected_group_ids = self.listbox_ctrl.get_selected_group_ids()
                selected_lb = []
            elif self.listbox_ctrl is not None:
                selected_meta_idx = self.listbox_ctrl.get_selected_metadata_indices()
                selected_lb = []
            else:
                selected_lb = self.view.listbox.get_selected_indices()

            if (not selected_lb) and (not selected_group_ids) and (self.listbox_ctrl is None or not selected_meta_idx):
                if is_group_view:
                    logger.warning("Export blocked: no groups selected in selected scope")
                    messagebox.showerror("Export", "No groups are selected. "
                                         "Please select groups in the list first.")
                else:
                    logger.warning("Export blocked: no images selected in selected scope")
                    messagebox.showerror("Export", "No images are selected. "
                                         "Please select images in the list first.")
                return
            if is_group_view:
                if not selected_group_ids:
                    # Fallback when listbox controller is unavailable.
                    all_visible_groups = [
                        group_id for group_id in self.model.metadata.groups(visible_only=True)
                        if group_id != "default"
                    ]
                    for i in selected_lb:
                        if i < len(all_visible_groups):
                            group_id = all_visible_groups[i]
                            if group_id not in selected_group_ids:
                                selected_group_ids.append(group_id)
                items = []
            else:
                if self.listbox_ctrl is not None:
                    selected_set = set(selected_meta_idx)
                    items = [(idx, meta) for idx, meta in all_visible if idx in selected_set]
                else:
                    # Fallback when listbox controller is unavailable.
                    items = [all_visible[i] for i in selected_lb if i < len(all_visible)]
        else:
            items = all_visible

        directory = askdirectory(title="Choose Export Folder")
        if not directory:
            logger.debug("Export canceled at directory selection")
            return

        ext = self.model.settings.export_format.lstrip(".")
        ext = "." + ext

        def convert_for_format(image):
            # JPEG/BMP don't support alpha — convert to RGB when needed.
            if ext.lower() in (".jpg", ".jpeg", ".bmp") and image.mode in ("RGBA", "LA", "P"):
                return image.convert("RGB")
            return image

        def build_subfolder(meta):
            if not do_subdivide:
                return directory
            parent_folder = os.path.basename(os.path.dirname(meta.nickname))
            if not parent_folder:
                return directory
            subfolder = os.path.join(directory, parent_folder)
            os.makedirs(subfolder, exist_ok=True)
            return subfolder

        grouped_item_indices = {}
        for idx, meta in items:
            grouped_item_indices.setdefault(meta.group, []).append(idx)

        if scope == "selected" and is_group_view:
            # In group view + selected scope, export only selected groups.
            group_ids = selected_group_ids
        else:
            group_ids = []
            if do_export_groups:
                for group_id in grouped_item_indices.keys():
                    if group_id == "default":
                        continue
                    group_ids.append(group_id)

        logger.info(
            "Starting export: scope=%s items=%d groups=%d histograms=%s stats=%s subdivide=%s directory=%s",
            scope,
            len(items),
            len(group_ids),
            do_export_histograms,
            do_export_stats,
            do_subdivide,
            directory,
        )

        if not items and not group_ids:
            messagebox.showinfo("Export", "No images or groups to export.")
            return

        total_exports = len(items) + len(group_ids)
        if do_export_histograms:
            total_exports += len(items) + len(group_ids)

        errors = {}
        export_count = 0
        with ProgressBar(title="Exporting Images", total=total_exports) as progress:
            for idx, meta in items:
                try:
                    image, _stats = self.model.make_image(idx)
                    image = convert_for_format(image)
                    stem = os.path.splitext(os.path.basename(meta.nickname))[0]
                    subfolder = build_subfolder(meta)
                    out_path = os.path.join(subfolder, stem + ext)
                    image.save(out_path)
                    export_count += 1
                except Exception as e:
                    logger.exception("Failed exporting image for %s", meta.nickname)
                    errors[meta.nickname] = e
                finally:
                    progress.step()

                if do_export_histograms:
                    try:
                        histogram, _stats = self.model.make_histogram(idx)
                        histogram = convert_for_format(histogram)
                        stem = os.path.splitext(os.path.basename(meta.nickname))[0]
                        subfolder = build_subfolder(meta)
                        out_path = os.path.join(subfolder, f"{stem}_histogram{ext}")
                        histogram.save(out_path)
                        export_count += 1
                    except Exception as e:
                        logger.exception("Failed exporting histogram for %s", meta.nickname)
                        errors[f"{meta.nickname} (histogram)"] = e
                    finally:
                        progress.step()

            for group_id in group_ids:
                try:
                    group_image, _stats = self.model.make_group_image(group_id)
                    group_image = convert_for_format(group_image)
                    safe_group_id = str(group_id).replace(os.sep, "_")
                    out_path = os.path.join(directory, f"group_{safe_group_id}{ext}")
                    group_image.save(out_path)
                    export_count += 1
                except Exception as e:
                    logger.exception("Failed exporting group image for group %s", group_id)
                    errors[f"group {group_id}"] = e
                finally:
                    progress.step()

                if do_export_histograms:
                    try:
                        group_histogram, _stats = self.model.make_group_histogram(group_id)
                        group_histogram = convert_for_format(group_histogram)
                        safe_group_id = str(group_id).replace(os.sep, "_")
                        out_path = os.path.join(directory, f"group_{safe_group_id}_histogram{ext}")
                        group_histogram.save(out_path)
                        export_count += 1
                    except Exception as e:
                        logger.exception("Failed exporting group histogram for group %s", group_id)
                        errors[f"group {group_id} (histogram)"] = e
                    finally:
                        progress.step()

        if errors:
            logger.warning("Export completed with %d failure(s)", len(errors))
            self.view.show_error(errors)
        else:
            logger.info("Export completed successfully with %d file(s)", export_count)
            messagebox.showinfo("Export", f"Exported {export_count} file(s) to:\n{directory}")
        if do_export_stats:
            logger.info("Exporting statistics CSV to %s", directory)
            self.model.export_stats(directory=directory)