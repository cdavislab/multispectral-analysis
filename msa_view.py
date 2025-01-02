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

        self.root.rowconfigure(1, weight=16)
        self.root.columnconfigure(1, weight=16)
        self.root.rowconfigure(3, weight=16)
        self.root.columnconfigure(3, weight=16)
        self.root.rowconfigure(5, weight=16)
        self.root.columnconfigure(5, weight=16)
        self.root.rowconfigure(14, weight=1)

        self.paned_window = self.build_paned_window()
        self.build_file_viewer(self.paned_window)
        self.build_image_viewer(self.paned_window)

        self.build_user_buttons()
        self.build_wavenumber_inputs()
        self.set_defaults()
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
        # frm.grid(row=0, column=0, rowspan=7, columnspan=2, sticky="nsew", padx=2, pady=2)
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
        # self.img_panel.grid(row=0, column=2, rowspan=9, columnspan=4, sticky="nsew", padx=2, pady=2)
        root.add(self.img_panel)
        # self.img_panel.grid_propagate(False)
        return
    def build_user_buttons(self):
        self.Button_Add = self.decorate(tk.Button(self.root, text="Add Files"))
        self.Button_Add.grid(row=7, column=0, rowspan=1, columnspan=2, sticky="nsew", padx=2)

        self.Button_Delete = self.decorate(tk.Button(self.root, text="Delete Files"))
        self.Button_Delete.grid(row=8, column=0, rowspan=1, columnspan=2, sticky="nsew", padx=2)

        self.Button_Analyze = self.decorate(tk.Button(self.root, text="Analyze"))
        # self.Button_Analyze.configure(bg=self.default_blue)
        self.Button_Analyze.grid(row=9, column=0, rowspan=1, columnspan=2, sticky="nsew", padx=2)

        self.Button_Filename = self.decorate(tk.Label(self.root, text="Filename", relief="groove"))
        self.Button_Filename.grid(row=7, column=2, rowspan=1, columnspan=4, sticky="nsew", padx=2)

        self.Button_Statistics = self.decorate(tk.Label(self.root, text="Statistics", relief="groove"))
        self.Button_Statistics.grid(row=8, column=2, rowspan=2, columnspan=4, sticky="nsew", padx=2)

    def build_wavenumber_inputs(self):
        # Natural Wavenumber
        nw_text = self.decorate(tk.Label(self.root, justify="left", text="Frequency 1:"))
        nw_text.grid(row=11, column=0, rowspan=1, columnspan=1, sticky="nsew", padx=(2,0), pady=2)
        
        nw = tk.StringVar()
        self.nw_entry = self.decorate(tk.Entry(self.root, textvariable=nw))
        self.nw_entry.grid(row=11, column=1, rowspan=1, columnspan=1, sticky="nsew", padx=(0,2), pady=2)

        # Natural Correction Wavenumber
        ncw_text = self.decorate(tk.Label(self.root, justify="left", text="Frequency 1 Correction:"))
        ncw_text.grid(row=11, column=2, rowspan=1, columnspan=1, sticky="nsew", pady=2)

        ncw = tk.StringVar()
        self.ncw_entry = self.decorate(tk.Entry(self.root, textvariable=ncw))
        self.ncw_entry.grid(row=11, column=3, rowspan=1, columnspan=1, sticky="nsew", padx=(0,2), pady=2)

        # Natural Correction Factor
        ncf_text = self.decorate(tk.Label(self.root,justify="left", text="Frequency 1 Correction Factor:"))
        ncf_text.grid(row=11, column=4, rowspan=1, columnspan=1, sticky="nsew", pady=2)

        natural_cf = tk.StringVar()
        self.ncf_entry = self.decorate(tk.Entry(self.root, textvariable=natural_cf))
        self.ncf_entry.grid(row=11, column=5, rowspan=1, columnspan=1, sticky="nsew", padx=(0,2), pady=2)

        # Label Wavenumber
        lw_text = self.decorate(tk.Label(self.root, justify="left", text="Frequency 2:"))
        lw_text.grid(row=12, column=0, rowspan=1, columnspan=1, sticky="nsew", pady=2)

        label_wavenum = tk.StringVar()
        self.lw_entry = self.decorate(tk.Entry(self.root, textvariable=label_wavenum))
        self.lw_entry.grid(row=12, column=1, rowspan=1, columnspan=1, sticky="nsew", padx=(0,2), pady=2)

        # Label Correction Wavenumber
        lcw_text = self.decorate(tk.Label(self.root, justify="left", text="Frequency 2 Correction:"))
        lcw_text.grid(row=12, column=2, rowspan=1, columnspan=1, sticky="nsew", pady=2)

        lcw = tk.StringVar()
        self.lcw_entry = self.decorate(tk.Entry(self.root, textvariable=lcw))
        self.lcw_entry.grid(row=12, column=3, rowspan=1, columnspan=1, sticky="nsew", padx=(0,2), pady=2)

        # Label Correction Factor
        lcf_text = self.decorate(tk.Label(self.root, justify="left", text="Frequency 2 Correction Factor:"))
        lcf_text.configure(justify="left")
        lcf_text.grid(row=12, column=4, rowspan=1, columnspan=1, sticky="nsew", pady=2)

        lcf = tk.StringVar()
        self.lcf_entry = self.decorate(tk.Entry(self.root, textvariable=lcf))
        self.lcf_entry.grid(row=12, column=5, rowspan=1, columnspan=1, sticky="nsew", padx=(0,2), pady=2)

        # Threshold
        threshold_text = self.decorate(tk.Label(self.root, justify="left", text="Threshold:"))
        threshold_text.grid(row=13, column=4, rowspan=1, columnspan=1, sticky="nsew", pady=(2,0))

        threshold = tk.StringVar()
        self.threshold_entry = self.decorate(tk.Entry(self.root, textvariable=threshold))
        self.threshold_entry.grid(row=13, column=5, rowspan=1, columnspan=1, sticky="nsew", pady=(2,0))

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

        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Preferences")
        self.file_menu.add_command(label="Export Statistics")
        self.file_menu.add_command(label="Export File List")
        self.file_menu.add_command(label="Import File List")
        self.file_menu.add_command(label="Export Settings")
        self.file_menu.add_command(label="Import Settings")

        self.show_single.set(True)
        self.show_ratio.set(True)
        self.view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="View", menu=self.view_menu)
        self.view_menu.add_checkbutton(label="Group View", onvalue=1, offvalue=0, variable=self.show_groups)
        self.view_menu.add_checkbutton(label="Histograms", onvalue=1, offvalue=0, variable=self.show_histograms)
        self.view_menu.add_checkbutton(label="Show Single-Wavenumber", onvalue=1, offvalue=0, variable=self.show_single)
        self.view_menu.add_checkbutton(label="Show Ratios", onvalue=1, offvalue=0, variable=self.show_ratio)
        self.view_menu.add_command(label="Full File Path")

        return

    def set_defaults(self):
        self.nw_entry.insert(0, "1744")
        self.lw_entry.insert(0, "1703")
        self.ncw_entry.insert(0, "1655")
        self.lcw_entry.insert(0, "1655")
        self.ncf_entry.insert(0, ".31")
        self.lcf_entry.insert(0, ".61")
        self.threshold_entry.insert(0, "0.15")
        self.show_groups = tk.BooleanVar()
        self.show_histograms = tk.BooleanVar()
        self.show_single = tk.BooleanVar()
        self.show_ratio = tk.BooleanVar()
        self.export_correction = tk.BooleanVar()
        self.export_threshold = tk.BooleanVar()
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

        bottom_menu_height = self.Button_Filename.winfo_height()*5
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
            "nw": self.nw_entry.get(),
            "lw": self.lw_entry.get(),
            "ncw": self.ncw_entry.get(),
            "lcw": self.lcw_entry.get(),
            "ncf": self.ncf_entry.get(),
            "lcf": self.lcf_entry.get(),
            "threshold": self.threshold_entry.get(),
            "export_folder": self.Button_ExportFolder.cget('text'),
            "show_groups": self.show_groups.get(),
            "show_histograms": self.show_histograms.get(),
            "show_single": self.show_single.get(),
            "show_ratio": self.show_ratio.get(),
        }
        return settings

    class PropertiesView:
        
        def __init__(self, root, export_filetype, export_correction, export_threshold):
            # Create a new window
            self.pref_window = tk.Toplevel(root)
            self.pref_window.title("Preferences")

            # Create a frame to hold the widgets
            self.pref_frame = tk.Frame(self.pref_window)
            self.pref_frame.pack()

            self.padx_label = (20,0)
            self.padx_entry = (0,20)
            self.padx_hint = (20,20)
            self.properties = dict()
            row = 0
            self.make_form("Export File Type", 
                           "Choose file extension for future exports (e.g. .jpg, .png, .tiff, etc.)",
                           "entry", export_filetype, export_filetype, row)
            row += 2

            separator = ttk.Separator(self.pref_frame, orient='horizontal')
            separator.grid(row=row, column=0, columnspan=2, sticky='ew')
            row += 1

            self.make_form("Export Corrections", 
                           "Export raw files after correction",
                           "checkbutton", export_correction, export_correction, row)
            row += 2

            self.make_form("Export Threshold", 
                           "Export raw files after thresholding",
                           "checkbutton", export_threshold, export_threshold, row)
            row += 2

            # Put button on the bottom to save and quit 
            self.save_button = tk.Button(self.pref_frame, text="Save")
            self.save_button.grid(row=row, column=0, columnspan=2, pady=(10,5))

        def make_form(self, title, hint, type_of_entry, variable, default_value, row):
            # Generalize making of the forms
            label = tk.Label(self.pref_frame, text=title)
            label.grid(row=row, column=0, sticky='w', padx=self.padx_label)
            if type_of_entry == "entry":
                entry = tk.Entry(self.pref_frame)
                entry.insert(0, default_value)
                entry.grid(row=row, column=1, sticky='we', padx=self.padx_entry)
            elif type_of_entry == "checkbutton":
                entry = tk.Checkbutton(self.pref_frame, variable=variable)
                entry.grid(row=row, column=1, sticky='w', padx=self.padx_entry)
            label_hint = tk.Label(self.pref_frame, text=hint, fg='gray')
            label_hint.grid(row=row+1, column=0, columnspan=2, sticky='w', padx=self.padx_hint)
            self.properties[title] = {"label": label, "entry": entry, "label_hint": label_hint}
            return
        
        def get_setting(self, title):
            return self.properties[title]["entry"].get()
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