import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk
from pathlib import Path
from PIL import Image, ImageTk

# View class to handle the GUI components
class MultispectralView:
    def __init__(self, root):
        self.root = root
        self.default_font = tkFont.nametofont("TkDefaultFont").actual()
        self.default_blue = "#08a1f7"
        # self.default_bg = "#1C1C1C"
        # self.default_fg = "#FCFEFE"
        self.default_bg = "#e9e9ed"
        self.default_fg = "#000000"
        self.setup_ui()
        
    # Function to setup the GUI layout and components
    def setup_ui(self):
        self.root.title("Multispectral Analysis")
        width = 800
        height = 500
        screenwidth = self.root.winfo_screenwidth()
        screenheight = self.root.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        self.root.geometry(alignstr)
        self.root.resizable(True, True)
        self.root.configure(bg=self.default_bg)

        for i in (1,3,5):
            self.root.rowconfigure(i, weight=16)
            self.root.columnconfigure(i, weight=16)
        self.root.rowconfigure(14, weight=1)

        self.paned_window = self.build_paned_window()
        self.build_file_viewer(self.paned_window)
        self.build_image_viewer(self.paned_window)

        self.build_user_buttons()
        self.build_wavenumber_inputs()
        self.build_menubar()

    def decorate(self,widget):
        font = tkFont.nametofont(widget.cget('font')).actual()
        default_family = 'Verdana'
        default_size = 10
        # default_bg = "#e9e9ed"
        # default_fg = "#000000"
        
        justify = "center"
        # Override default if widget's font is already set
        if widget.cget('justify') != 'center':
            justify = widget.cget('justify')
        if font['family'] != self.default_font['family']:
            family = font['family']
        if font['size'] != self.default_font['size']:
            size = font['size']
        widget.configure(bg=self.default_bg, fg=self.default_fg, justify=justify, font=(default_family, default_size))
        return widget

    def build_paned_window(self):
        paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned_window.grid(row=0, column=0, rowspan=7, columnspan=16, sticky="nsew", padx=2, pady=2)  # Fill the entire window
        return paned_window
    def build_file_viewer(self, root):
        frm = tk.Frame(root)
        scrollbar = tk.Scrollbar(frm, orient="horizontal")
        scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.ListBox_1 = self.decorate(tk.Listbox(frm, xscrollcommand=scrollbar.set))
        self.ListBox_1.configure(fg="#333333", borderwidth="1px")
        self.ListBox_1.pack(expand=True, fill=tk.BOTH)
        scrollbar.config(command=self.ListBox_1.xview)
        root.add(frm)
        return
    def build_image_viewer(self, root):
        self.img_panel = tk.Label(root, bg='gray')
        self.panel_img = ""
        root.add(self.img_panel)
        return
    def build_user_buttons(self):
        self.Button_Add = self.decorate(tk.Button(self.root, text="Add Files"))
        self.Button_Add.grid(row=7, column=0, rowspan=1, columnspan=2, sticky="nsew", padx=2)

        self.Button_Delete = self.decorate(tk.Button(self.root, text="Delete Files"))
        self.Button_Delete.grid(row=8, column=0, rowspan=1, columnspan=2, sticky="nsew", padx=2)

        self.Button_Analyze = self.decorate(tk.Button(self.root, text="Analyze"))
        self.Button_Analyze.grid(row=9, column=0, rowspan=1, columnspan=2, sticky="nsew", padx=2)

        self.Button_Filename = self.decorate(tk.Label(self.root, text="Filename", relief="groove"))
        self.Button_Filename.grid(row=7, column=2, rowspan=1, columnspan=4, sticky="nsew", padx=2)

        self.Button_Statistics = self.decorate(tk.Label(self.root, text="Statistics", relief="groove"))
        self.Button_Statistics.grid(row=8, column=2, rowspan=2, columnspan=4, sticky="nsew", padx=2)

    def build_wavenumber_inputs(self):
        # Define configuration details for labels and entries
        widgets_config = [
            {"text": "Frequency 1:", "row": 11, "col": 0, "entry_var": "freq1"},
            {"text": "Frequency 1 Correction:", "row": 11, "col": 2, "entry_var": "freq1c"},
            {"text": "Frequency 1 Correction Factor:", "row": 11, "col": 4, "entry_var": "freq1cf"},
            {"text": "Frequency 2:", "row": 12, "col": 0, "entry_var": "freq2"},
            {"text": "Frequency 2 Correction:", "row": 12, "col": 2, "entry_var": "freq2c"},
            {"text": "Frequency 2 Correction Factor:", "row": 12, "col": 4, "entry_var": "freq2cf"},
            {"text": "Threshold:", "row": 13, "col": 4, "entry_var": "threshold"},
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

        bottom_spacer = self.decorate(tk.Label(self.root, text=""))
        bottom_spacer.grid(row=14, column=0, rowspan=1, columnspan=6, sticky="nsew")

    def build_menubar(self):
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
        self.show_groups = tk.BooleanVar()
        self.show_histograms = tk.BooleanVar()
        self.show_single = tk.BooleanVar()
        self.show_ratio = tk.BooleanVar()
        self.view_mode = tk.StringVar(value="full")
        return

    def get_shape(self, widget):
        geometry = widget.winfo_geometry()  # Get the geometry string
        # Split the string to extract the width and height
        width, height = geometry.split('x')[0], geometry.split('x')[1].split('+')[0]
        return int(width), int(height)

    def display(self, img_path):
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

        img = img.resize((int(original_width*scalar)-20, int(original_height*scalar)-20))
        self.panel_img = ImageTk.PhotoImage(img)
        self.img_panel.configure(image=self.panel_img)
        return
    
    def show_error(self, errors):
        error_str = "Could not add the following files:\n"
        for error in errors:
            error_str += error + "\n"
        tk.messagebox.showerror("Error", error_str)
        return
    
    def get_settings(self):
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
            if len(args) != 4:
                raise ValueError("Expected exactly 4 arguments. Got {}".format(len(args)))

            (export_filetype,
            save_correction_freq1_val,
            save_correction_freq2_val,
            export_threshold_val) = args

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
            return

        def make_label(self, label):
            #Make a bold label
            label = tk.Label(self.pref_frame, text=label, font=("Verdana", 10, "bold"))
            label.grid(row=self.row, column=0, columnspan=1, sticky='w', padx=self.padx_label)
            self.row += 1
            return

        def make_separator(self):
            separator = ttk.Separator(self.pref_frame, orient='horizontal')
            separator.grid(row=self.row, column=0, columnspan=5, sticky='ew')
            self.row += 1
            return
        def make_form(self, title, hint, type_of_entry, variable):
            # Generalize making of the forms
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
            # Generalize making of the forms
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
            return self.properties[title]["entry"].get()
        
        def get_setting_keys(self):
            return self.properties.keys()
    class ImagePropertiesView(PropertiesView):
        def __init__(self, root, *args):
            super().__init__(root, *args)
            self.pref_window.title("Image Preferences")
            self.pref_frame.pack()
            return

        def _create_widgets(self, *args):
            [font, font_size, font_weight, cmap, vmin, vmax, cunits, pixel_scale,
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

            self.make_label("Scale")
            self.make_form("Pixel Scale", "Change the scale of the pixels", "entry", pixel_scale)
            self.make_form("Scale Bar Units", "Units of the scale bar", "entry", scale_bar_units)
            self.make_form("Scale Bar Color", "(e.g. white or black)", "entry", scale_bar_color)
            self.make_form("Scale Bar Location", "(e.g. upper/lower left)", "entry", scale_bar_location)
            self.make_form("Scale Bar Fixed Value", "(e.g. '10' for 10 units)", "entry", scale_bar_fixed_value)

            self.make_label("Extra")
            self.make_form("Number of Tick Marks", "Number of axis tick markers", "entry", num_ticks)
            return
        
    class ProgressBar(tk.Tk):
        def __init__(self, title="Progress Bar"):
            super().__init__()
            self.title(title)
            self.geometry("400x150")

            # Create a canvas for the progress bar
            self.canvas = tk.Canvas(self, width=300, height=30, bg='white', highlightthickness=1, highlightbackground='black')
            self.canvas.pack(pady=40)
            
            self.progress = 0  # Initialize progress value
            self.canvas.delete("progress")
            self.update_progress(0)

        def update_progress(self, value):
            """Update the progress bar on the canvas."""
            self.canvas.delete("progress")  # Clear previous progress
            fill_width = (value / 100) * 300  # Calculate the fill width
            self.canvas.create_rectangle(0, 0, fill_width, 30, fill="green", tags="progress")
            self.update_idletasks()  # Refresh the UI