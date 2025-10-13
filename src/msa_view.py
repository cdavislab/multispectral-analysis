import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk
from PIL import Image, ImageTk

class MultispectralView:
    """View class to handle the GUI components for multispectral analysis."""

    DEFAULT_FONT_FAMILY = 'Verdana'
    DEFAULT_FONT_SIZE = 10
    DEFAULT_BG = "#e9e9ed"
    DEFAULT_FG = "#000000"
    DEFAULT_BLUE = "#08a1f7"

    def __init__(self, root: tk.Tk):
        """Initialize the main window and default styles."""
        self.root = root
        self.default_font = tkFont.nametofont("TkDefaultFont").actual()
        self.setup_ui()

    def setup_ui(self):
        """Configure window size, layout, and add main UI components"""
        self.root.title("Multispectral Analysis")
        width = 800
        height = 500
        screenwidth = self.root.winfo_screenwidth()
        screenheight = self.root.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        self.root.geometry(alignstr)
        self.root.resizable(True, True)
        self.root.configure(bg=self.DEFAULT_BG)

        for i in (3,5):
            self.root.rowconfigure(i, weight=16)
            self.root.columnconfigure(i, weight=16)
        self.root.rowconfigure(14, weight=1)

        self.paned_window = self.build_paned_window()
        self.build_file_viewer(self.paned_window)
        self.build_image_viewer(self.paned_window)

        self.build_user_buttons()
        self.build_wavenumber_inputs()
        self.build_menubar()

    def decorate(self, widget: tk.Widget) -> tk.Widget:
        """Apply default styling to widgets."""
        widget.configure(
            bg=self.DEFAULT_BG,
            fg=self.DEFAULT_FG,
            justify="center",
            font=(self.DEFAULT_FONT_FAMILY, self.DEFAULT_FONT_SIZE)
        )
        return widget

    def build_paned_window(self) -> tk.PanedWindow:
        """Create and place the main paned window."""
        paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned_window.grid(row=0, column=0, rowspan=7, columnspan=16, sticky="nsew", padx=2, pady=2)  # Fill the entire window
        return paned_window
    def build_file_viewer(self, root):
        """Build the file list viewer with scrollbar."""
        frm = tk.Frame(root)
        scrollbar = tk.Scrollbar(frm, orient="horizontal")
        scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.ListBox_1 = self.decorate(tk.Listbox(frm, xscrollcommand=scrollbar.set, selectmode=tk.MULTIPLE))
        self.ListBox_1.configure(fg="#333333", borderwidth="1px")
        self.ListBox_1.pack(expand=True, fill=tk.BOTH)
        scrollbar.config(command=self.ListBox_1.xview)
        root.add(frm)
        return
    def build_image_viewer(self, root):
        """Build the image display panel."""
        self.img_panel = tk.Label(root, bg='gray')
        self.panel_img = ""
        root.add(self.img_panel)
        return
    def build_user_buttons(self):
        """Create and place main user action buttons and labels."""
        self.Button_Add = self.decorate(tk.Button(self.root, text="Add Files"))
        self.Button_Add.grid(row=7, column=0, rowspan=1, columnspan=1, sticky="nsew", padx=2)

        self.Button_Delete = self.decorate(tk.Button(self.root, text="Delete Files"))
        self.Button_Delete.grid(row=8, column=0, rowspan=1, columnspan=1, sticky="nsew", padx=2)

        self.Button_Analyze = self.decorate(tk.Button(self.root, text="Analyze"))
        self.Button_Analyze.grid(row=9, column=0, rowspan=1, columnspan=1, sticky="nsew", padx=2)

        self.Button_Frequency1 = self.decorate(tk.Button(self.root, text="Frequency 1", command=self.open_multi_corrections_dialog))
        self.Button_Frequency1.grid(row=7, column=1, rowspan=1, columnspan=1, sticky="nsew", padx=2)

        self.Button_Frequency2 = self.decorate(tk.Button(self.root, text="Frequency 2", command=self.open_multi_corrections_dialog))
        self.Button_Frequency2.grid(row=8, column=1, rowspan=1, columnspan=1, sticky="nsew", padx=2)

        self.Button_ExportFolder = self.decorate(tk.Button(self.root, text="Export Folder"))
        self.Button_ExportFolder.grid(row=9, column=1, rowspan=1, columnspan=1, sticky="nsew", padx=2)

        self.Button_Filename = self.decorate(tk.Label(self.root, text="Filename", relief="groove"))
        self.Button_Filename.grid(row=7, column=2, rowspan=1, columnspan=4, sticky="nsew", padx=2)

        self.Button_Statistics = self.decorate(tk.Label(self.root, text="Statistics", relief="groove"))
        self.Button_Statistics.grid(row=8, column=2, rowspan=2, columnspan=4, sticky="nsew", padx=2)

    def build_wavenumber_inputs(self):
        """Build the input fields for wavenumber and export folder."""
        return
        # Define configuration details for labels and entries
        # widgets_config = [
        #     {"text": "Frequency 1:", "row": 11, "col": 0, "entry_var": "freq1"},
        #     {"text": "Frequency 1 Correction:", "row": 11, "col": 2, "entry_var": "freq1c"},
        #     {"text": "Frequency 1 Correction Factor:", "row": 11, "col": 4, "entry_var": "freq1cf"},
        #     {"text": "Frequency 2:", "row": 12, "col": 0, "entry_var": "freq2"},
        #     {"text": "Frequency 2 Correction:", "row": 12, "col": 2, "entry_var": "freq2c"},
        #     {"text": "Frequency 2 Correction Factor:", "row": 12, "col": 4, "entry_var": "freq2cf"},
        #     {"text": "Threshold:", "row": 13, "col": 4, "entry_var": "threshold"},
        # ]
        widgets_config = [
            {"text": "Frequency 1:", "row": 7, "col": 1, "entry_var": "freq1"},
            {"text": "Frequency 2:", "row": 8, "col": 1, "entry_var": "freq2"}
        ]

        # Store references to StringVars and Entries
        self.string_vars = {}
        self.entries = {}

        for config in widgets_config:
            # Create and place labels
            label = self.decorate(tk.Label(self.root, justify="left", text=config["text"]))
            label.grid(row=config["row"], column=config["col"], rowspan=1, columnspan=1, sticky="nsew", padx=(2 if config["col"] % 2 == 0 else 0, 2), pady=2)

            # Create, store, and place entries
            entry_var = tk.StringVar()
            entry = self.decorate(tk.Entry(self.root, textvariable=entry_var, insertbackground="gray", cursor='xterm gray'))
            entry.grid(row=config["row"], column=config["col"] + 1, rowspan=1, columnspan=1, sticky="nsew", padx=(0, 2), pady=2)

            self.string_vars[config["entry_var"]] = entry_var
            self.entries[config["entry_var"]] = entry

        # Export Folder
        export_folder_text = self.decorate(tk.Label(self.root, justify="center", text="Export Folder:"))
        export_folder_text.grid(row=13, column=0, rowspan=1, columnspan=1, sticky="nsew", padx=(2,0), pady=(2,0))

        self.Button_ExportFolder = self.decorate(tk.Button(self.root, justify="left", text="Export Folder Path", relief="sunken"))
        self.Button_ExportFolder.grid(row=13, column=1, rowspan=1, columnspan=3, sticky="nsew", padx=(0,2), pady=(2,0))

        # Add button to open multiple corrections dialog
        self.Button_MultiCorrections = self.decorate(
            tk.Button(self.root, text="Set Multiple Corrections", command=self.open_multi_corrections_dialog)
        )
        self.Button_MultiCorrections.grid(row=13, column=5, rowspan=1, columnspan=1, sticky="nsew", padx=(2,2), pady=(2,0))

        bottom_spacer = self.decorate(tk.Label(self.root, text=""))
        bottom_spacer.grid(row=14, column=0, rowspan=1, columnspan=6, sticky="nsew")

    def build_menubar(self):
        """Build the menu bar and menus for file/view/path options."""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        self.initialize_menu_vars()

        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        labels = ["Preferences", "Image Config","Export Statistics", "Export File List",
                  "Import File List", "Export Settings", "Import Settings"]
        for label in labels:
            self.file_menu.add_command(label=label)
        
        self.view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="View", menu=self.view_menu)
        labels = ("Group View", "Histograms", "Show Single-Wavenumber", "Show Ratios")
        variables = (self.show_groups, self.show_histograms, self.show_single, self.show_ratio)
        for label, variable in zip(labels, variables):
            self.view_menu.add_checkbutton(label=label, onvalue=1, offvalue=0,
                                           variable=variable)
        
        self.fpath_menu = tk.Menu(self.view_menu, tearoff=0)
        self.view_menu.add_cascade(label="File Path", menu=self.fpath_menu)
        self.fpath_menu.add_radiobutton(label="View Full Path", variable=self.view_mode, value="full")
        self.fpath_menu.add_radiobutton(label="View Parent", variable=self.view_mode, value="parent")
        self.fpath_menu.add_radiobutton(label="View File Only", variable=self.view_mode, value="file")


        return

    def initialize_menu_vars(self):
        """Initialize Tkinter variables for menu state."""
        self.show_groups = tk.BooleanVar()
        self.show_histograms = tk.BooleanVar()
        self.show_single = tk.BooleanVar()
        self.show_ratio = tk.BooleanVar()
        self.view_mode = tk.StringVar(value="full")
        return

    def get_shape(self, widget: tk.Widget) -> tuple[int, int]:
        """Utility: get widget width and height."""
        geometry = widget.winfo_geometry()  # Get the geometry string
        # Split the string to extract the width and height
        width, height = geometry.split('x')[0], geometry.split('x')[1].split('+')[0]
        return int(width), int(height)

    def display(self, img_path: str):
        """Display an image in the image panel, resizing as needed."""
        screen_width, screen_height = self.get_shape(self.root)
        sash_position = self.paned_window.sash_coord(0)[0]
        img_width = screen_width - sash_position

        bottom_menu_height = self.Button_Filename.winfo_height()*7
        img_height = screen_height - bottom_menu_height

        img = Image.open(img_path)
        original_width, original_height = img.size

        # Resize the image to fit the window while maintaining the aspect ratio
        scalar1 = img_width / original_width
        scalar2 = img_height / original_height
        scalar = min(scalar1, scalar2)

        # Fix: Avoid negative dimensions when resizing
        img = img.resize((
            max(1, int(original_width * scalar) - 20),
            max(1, int(original_height * scalar) - 20)
        ))
        self.panel_img = ImageTk.PhotoImage(img)
        self.img_panel.configure(image=self.panel_img)
        return
    
    def show_error(self, errors: dict):
        """Show error dialog for failed file additions."""
        error_str = "Could not add the following files:\n"
        for error in errors:
            error_str += error + "\n"
        tk.messagebox.showerror("Error", error_str)
        return
    
    def get_settings(self) -> dict:
        """Gather current settings from the UI."""
        settings = {
            'freq1': self.entries['freq1'].get(),
            'freq2': self.entries['freq2'].get(),
            'freq1c': self.entries['freq1c'].get(),
            'freq2c': self.entries['freq2c'].get(),
            'freq1cf': self.entries['freq1cf'].get(),
            'freq2cf': self.entries['freq2cf'].get(),
            'threshold': self.entries['threshold'].get(),
            "show_groups": self.show_groups.get(),
            "show_histograms": self.show_histograms.get(),
            "show_single": self.show_single.get(),
            "show_ratio": self.show_ratio.get(),
            "view_mode": self.view_mode.get()
        }
        return settings

    class PropertiesView:
        """Dialog for editing main preferences."""
        def __init__(self, root, *args):
            # Create a new window
            self.pref_window = tk.Toplevel(root)
            self.pref_window.title("Preferences")

            # Create a frame to hold the widgets
            self.pref_frame = tk.Frame(self.pref_window)
            self.pref_frame.pack()

            self.padx_label = (20,0)
            self.padx_entry = (0,20)
            self.padx_hint = (20,20)
            self.row = 0
            self.properties = dict()

            self._create_widgets(*args)

            # Put button on the bottom to save and quit 
            self.save_button = tk.Button(self.pref_frame, text="Save")
            self.save_button.grid(row=self.row, column=4, columnspan=1, pady=(10,5))

            self.pref_frame.grid_columnconfigure(0, weight=3)
            for i in range(1,5):
                self.pref_frame.grid_columnconfigure(i, weight=1)

        def _create_widgets(self, *args):
            # Build the form fields for preferences
            if len(args) != 9:
                raise ValueError("Expected exactly 9 arguments. Got {}".format(len(args)))

            (export_filetype,
            save_correction_freq1_val,
            save_correction_freq2_val,
            export_threshold_val,
            freq1_label, freq2_label,
            freq1c_label, freq2c_label,
            ratio_label) = args

            save_correction_freq1 = tk.BooleanVar()
            save_correction_freq1.set(save_correction_freq1_val)
            save_correction_freq2 = tk.BooleanVar()
            save_correction_freq2.set(save_correction_freq2_val)
            export_threshold = tk.BooleanVar()
            export_threshold.set(export_threshold_val)

            # TODO: Add bold labels, move image entries to separate window, add functionality (later), add error checking (later)
            self.make_label("Export")
            self.make_form("Export File Type", 
                           "Choose file extension for future exports (e.g. .jpg, .png, .tiff, etc.)",
                           "entry", export_filetype)
            self.make_double_form("Export Corrections", 
                           "Export raw files after correction",
                           "checkbutton", ("Freq 1:", save_correction_freq1),
                           ("Freq 2:", save_correction_freq2))
            self.make_form("Export Threshold", 
                           "Export raw files after thresholding",
                           "checkbutton", export_threshold)
            self.make_label("Labels")
            self.make_form("Frequency 1 Label", 
                           "Label for frequency 1 in group images",
                           "entry", freq1_label)
            self.make_form("Frequency 2 Label", 
                           "Label for frequency 2 in group images",
                           "entry", freq2_label)
            self.make_form("Frequency 1 Correction Label", 
                           "Label for frequency 1 correction in group images",
                           "entry", freq1c_label)
            self.make_form("Frequency 2 Correction Label", 
                           "Label for frequency 2 correction in group images",
                           "entry", freq2c_label)
            self.make_form("Ratio Label", 
                           "Label for ratio in group images",
                           "entry", ratio_label)
            return

        def make_label(self, label):
            # Make a bold section label
            #Make a bold label
            label = tk.Label(self.pref_frame, text=label, font=("Verdana", 10, "bold"))
            label.grid(row=self.row, column=0, columnspan=1, sticky='w', padx=self.padx_label)
            self.row += 1
            return

        def make_separator(self):
            # Add a separator line
            separator = ttk.Separator(self.pref_frame, orient='horizontal')
            separator.grid(row=self.row, column=0, columnspan=5, sticky='ew')
            self.row += 1
            return
        def make_form(self, title, hint, type_of_entry, variable):
            # Generalized form field creation
            label = tk.Label(self.pref_frame, text=title)
            label.grid(row=self.row, column=0, sticky='w', padx=self.padx_label)
            if type_of_entry == "entry":
                entry = tk.Entry(self.pref_frame)
                entry.insert(0, variable)
                entry.grid(row=self.row, column=1, columnspan=4,sticky='we', padx=self.padx_entry)
            elif type_of_entry == "checkbutton":
                entry = variable
                checkbox = tk.Checkbutton(self.pref_frame, variable=entry)
                checkbox.grid(row=self.row, column=1, columnspan=4, sticky='w', padx=self.padx_entry)
            label_hint = tk.Label(self.pref_frame, text=hint, fg='gray')
            label_hint.grid(row=self.row+1, column=0, columnspan=5, sticky='w', padx=self.padx_hint)
            self.properties[title] = {"label": label, "entry": entry, "label_hint": label_hint}
            self.row += 2
            return
        
        def make_double_form(self, title, hint, type_of_entry, form1, form2):
            # Generalized double form field creation
            label = tk.Label(self.pref_frame, text=title)
            label.grid(row=self.row, column=0, sticky='w', padx=self.padx_label)
            label_hint = tk.Label(self.pref_frame, text=hint, fg='gray')
            label_hint.grid(row=self.row+1, column=0, columnspan=5, sticky='w', padx=self.padx_hint)
            column_num = 1
            if type_of_entry == "entry":
                for form in (form1, form2):
                    subtitle, variable = form
                    sublabel = tk.Label(self.pref_frame, text=subtitle)
                    sublabel.grid(row=self.row, column=column_num, sticky='w')
                    column_num += 1
                    entry = tk.Entry(self.pref_frame, width=5)
                    entry.grid(row=self.row, column=column_num, columnspan=1, sticky='w', padx=self.padx_entry)
                    entry.insert(0, variable)
                    column_num += 1
                    self.properties[subtitle] = {"label": sublabel, "entry": entry, "label_hint": label_hint}
            elif type_of_entry == "checkbutton":
                for form in (form1, form2):
                    subtitle, entry = form
                    sublabel = tk.Label(self.pref_frame, text=subtitle)
                    sublabel.grid(row=self.row, column=column_num, sticky='w')
                    column_num += 1
                    checkbox = tk.Checkbutton(self.pref_frame, variable=entry)
                    checkbox.grid(row=self.row, column=column_num, columnspan=1, sticky='w', padx=0)
                    column_num += 1
                    self.properties[subtitle] = {"label": sublabel, "entry": entry, "label_hint": label_hint}
            self.row += 2
            return

        def get_setting(self, title):
            # Get value from a form field
            return self.properties[title]["entry"].get()
        
        def get_setting_keys(self):
            # Get all setting keys
            return self.properties.keys()
    class ImagePropertiesView(PropertiesView):
        """Dialog for editing image preferences."""
        def __init__(self, root, *args):
            super().__init__(root, *args)
            self.pref_window.title("Image Preferences")
            self.pref_frame.pack()
            return

        def _create_widgets(self, *args):
            # Build the form fields for image preferences
            [font, font_size, font_weight, cmap, vmin, vmax, cunits,
             ratio_vmin, ratio_vmax, ratio_cunits, pixel_scale,
             scale_bar_units, scale_bar_color,scale_bar_location,
             scale_bar_fixed_value,num_ticks] = args
            
            self.make_label("Font")
            self.make_form("Font", "Font of axes text", "entry", font) # TODO: Make pop up for wrong font and check for it!
            self.make_form("Font Size", "Font size of axes text", "entry", font_size)
            self.make_form("Font Weight", "(e.g. light, normal, heavy, bold)", "entry", font_weight)
            self.make_label("Color Bar")
            self.make_form("Color Map", "Choose Matplotlib colormap", "entry", cmap)
            self.make_double_form("Scale", "Minimum and max of the color bar", "entry", ("Min", vmin), ("Max", vmax))
            self.make_form("Units", "Units of the color bar", "entry", cunits)
            self.make_double_form("Scale", "Minimum and max of ratio color bar", "entry", ("rMin", ratio_vmin), ("rMax", ratio_vmax))
            self.make_form("Ratio Units", "Units of the ratio color bar", "entry", ratio_cunits)
            self.make_label("Scale")
            self.make_form("Pixel Scale", "Change the scale of the pixels", "entry", pixel_scale)
            self.make_form("Scale Bar Units", "Units of the scale bar", "entry", scale_bar_units)
            self.make_form("Scale Bar Color", "(e.g. white or black)", "entry", scale_bar_color)
            self.make_form("Scale Bar Location", "(e.g. upper/lower left)", "entry", scale_bar_location)
            self.make_form("Scale Bar Fixed Value", "(e.g. '10' for 10 units)", "entry", scale_bar_fixed_value)

            self.make_label("Extra")
            self.make_form("Number of Tick Marks", "Number of axis tick markers", "entry", num_ticks)
            return
        
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

        def update_progress(self, value: float):
            """Update the progress bar on the canvas."""
            self.canvas.delete("progress")
            fill_width = (value / 100) * 300
            self.canvas.create_rectangle(0, 0, fill_width, 30, fill="green", tags="progress")
            self.update()

    def open_multi_corrections_dialog(self):
        """Open dialog to input multiple corrections and factors."""
        dialog = self.MultiCorrectionsDialog(self.root)
        if dialog.result is not None:
            # Store results for controller/model access
            self.multiple_corrections = dialog.result['corrections']
            self.multiple_factors = dialog.result['factors']

    class MultiCorrectionsDialog(tk.Toplevel):
        """Dialog for entering multiple correction steps with operations and output keys."""
        def __init__(self, parent):
            super().__init__(parent)
            self.title("Multiple Corrections")
            self.geometry("700x400")
            self.steps = []
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
            headers = ["#", "keyword", "operation", "keyword2", "value", "output key", "", ""]
            for col, header in enumerate(headers):
                tk.Label(self.left_pane, text=header, font=("Verdana", 9, "bold")).grid(row=0, column=col, padx=2, pady=2)

            self.step_rows = []
            self.next_row = 1

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
            self.save_button = tk.Button(self.right_pane, text="Save", width=22, command=self.save_and_close)
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
                keyword.insert(0, step.get("keyword", ""))
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
                del_btn = tk.Button(self.left_pane, text="✕", width=2, fg="red", command=lambda idx=idx-1: self.delete_step_row(idx))
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
                    "keyword": dialog.result["keyword1"],
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
                    "keyword": dialog.result["keyword"],
                    "operation": "threshold",
                    "keyword2": "",
                    "value": dialog.result["threshold"],
                    "output_key": dialog.result["output_key"]
                }
                self.add_step_row(step)

        def save_and_close(self):
            """Collect all steps and close dialog."""
            self.steps = []
            for row in self.step_rows:
                _, keyword, operation, keyword2, value, output_key, _, _, _ = row
                step = {
                    "keyword": keyword.get().strip(),
                    "operation": operation.get().strip(),
                    "keyword2": keyword2.get().strip(),
                    "value": value.get().strip(),
                    "output_key": output_key.get().strip()
                }
                if step["keyword"] and step["operation"] and step["output_key"]:
                    self.steps.append(step)
            self.result = self.steps
            self.destroy()

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
                    "keyword": self.keyword.get().strip(),
                    "threshold": self.threshold.get().strip(),
                    "output_key": self.output_key.get().strip()
                }
                self.destroy()