import tkinter as tk
import tkinter.font as tkFont
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
        
        # self.root.bind("<Configure>", self.on_resize)

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

        self.Button_Filename = self.decorate(tk.Button(self.root, text="Filename"))
        self.Button_Filename.grid(row=7, column=2, rowspan=1, columnspan=4, sticky="nsew", padx=2)

        self.Button_Statistics = self.decorate(tk.Button(self.root, text="Statistics"))
        self.Button_Statistics.grid(row=8, column=2, rowspan=2, columnspan=4, sticky="nsew", padx=2)

    def build_wavenumber_inputs(self):
        # Natural Wavenumber
        nw_text = self.decorate(tk.Label(self.root, justify="left", text="Natural (cm-1):"))
        nw_text.grid(row=11, column=0, rowspan=1, columnspan=1, sticky="nsew", padx=(2,0), pady=2)
        
        nw = tk.StringVar()
        self.nw_entry = self.decorate(tk.Entry(self.root, textvariable=nw))
        self.nw_entry.grid(row=11, column=1, rowspan=1, columnspan=1, sticky="nsew", padx=(0,2), pady=2)

        # Natural Correction Wavenumber
        ncw_text = self.decorate(tk.Label(self.root, justify="left", text="Natural Correction (cm-1):"))
        ncw_text.grid(row=11, column=2, rowspan=1, columnspan=1, sticky="nsew", pady=2)

        ncw = tk.StringVar()
        self.ncw_entry = self.decorate(tk.Entry(self.root, textvariable=ncw))
        self.ncw_entry.grid(row=11, column=3, rowspan=1, columnspan=1, sticky="nsew", padx=(0,2), pady=2)

        # Natural Correction Factor
        ncf_text = self.decorate(tk.Label(self.root,justify="left", text="Natural Correction Factor:"))
        ncf_text.grid(row=11, column=4, rowspan=1, columnspan=1, sticky="nsew", pady=2)

        natural_cf = tk.StringVar()
        self.ncf_entry = self.decorate(tk.Entry(self.root, textvariable=natural_cf))
        self.ncf_entry.grid(row=11, column=5, rowspan=1, columnspan=1, sticky="nsew", padx=(0,2), pady=2)

        # Label Wavenumber
        lw_text = self.decorate(tk.Label(self.root, justify="left", text="Label (cm-1):"))
        lw_text.grid(row=12, column=0, rowspan=1, columnspan=1, sticky="nsew", pady=2)

        label_wavenum = tk.StringVar()
        self.lw_entry = self.decorate(tk.Entry(self.root, textvariable=label_wavenum))
        self.lw_entry.grid(row=12, column=1, rowspan=1, columnspan=1, sticky="nsew", padx=(0,2), pady=2)

        # Label Correction Wavenumber
        lcw_text = self.decorate(tk.Label(self.root, justify="left", text="Label Correction (cm-1):"))
        lcw_text.grid(row=12, column=2, rowspan=1, columnspan=1, sticky="nsew", pady=2)

        lcw = tk.StringVar()
        self.lcw_entry = self.decorate(tk.Entry(self.root, textvariable=lcw))
        self.lcw_entry.grid(row=12, column=3, rowspan=1, columnspan=1, sticky="nsew", padx=(0,2), pady=2)

        # Label Correction Factor
        lcf_text = self.decorate(tk.Label(self.root, justify="left", text="Label Correction Factor:"))
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

        self.settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Settings", menu=self.settings_menu)
        self.settings_menu.add_command(label="Open Config")
        self.settings_menu.add_command(label="Save Config")

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

    def display(self, img_path):
        geometry = self.root.winfo_geometry()  # Get the geometry string
        # Split the string to extract the width and height
        screen_width, screen_height = geometry.split('x')[0], geometry.split('x')[1].split('+')[0]
        sash_position = self.paned_window.sash_coord(0)[0]
        img_width = int(screen_width) - sash_position
        # listbox_width = sash_position
        # img
        # img_width = int(int(screen_width)//1.8)
        bottom_menu_height = self.Button_Filename.winfo_height()*5
        img_height = int(screen_height) - bottom_menu_height

        img = Image.open(img_path)
        original_width, original_height = img.size

        # Resize the image to fit the window while maintaining the aspect ratio
        scalar1 = img_width / original_width
        scalar2 = img_height / original_height
        scalar = min(scalar1, scalar2)

        img = img.resize((int(original_width*scalar), int(original_height*scalar)))
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
        
        def __init__(self, root, export_filetype):
            # Create a new window
            self.pref_window = tk.Toplevel(root)
            self.pref_window.title("Preferences")
            self.pref_window.geometry("400x400")
            # Create a frame to hold the widgets
            self.pref_frame = tk.Frame(self.pref_window)
            self.pref_frame.pack(expand=True, fill='both')
            # Create the widgets
            self.export_filetype_label= tk.Label(self.pref_frame, text="Export File Type (e.g. .jpg, .png, .tiff, etc.)")
            self.export_filetype_label.grid(row=0, column=0, sticky='w')
            self.export_filetype_entry = tk.Entry(self.pref_frame)
            self.export_filetype_entry.insert(0, export_filetype)
            self.export_filetype_entry.grid(row=0, column=1)
            self.export_filetype_hint = tk.Label(self.pref_frame, text="Choose the main file extension for future exports", fg='gray')
            self.export_filetype_hint.grid(row=1, column=0, columnspan=2, sticky='w')
            # self.export_fig_label = tk.Label(self.pref_frame, text="Export .fig")
            # self.export_fig_label.grid(row=2, column=0, sticky='w')
            # self.export_fig_checkbox = tk.Checkbutton(self.pref_frame, variable=export_fig)
            # self.export_fig_checkbox.grid(row=2, column=1)
            # self.export_fig_hint = tk.Label(self.pref_frame, text="Choose whether future files should be exported as .fig as well", fg='gray')
            # self.export_fig_hint.grid(row=3, column=0, columnspan=2, sticky='w')

            # Put button on the bottom to save and quit 
            self.save_button = tk.Button(self.pref_frame, text="Save")
            self.save_button.grid(row=4, column=0, columnspan=2)

        