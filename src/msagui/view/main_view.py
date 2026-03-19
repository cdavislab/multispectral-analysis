import tkinter as tk
import tkinter.font as tkFont
import tkinter.messagebox as messagebox

from msagui.view.display import DisplayView, ListboxView, WidgetsView
from msagui.view.defaults import ViewDefaults

class MultispectralView():
    """View class to handle the GUI components for multispectral analysis."""
    def __init__(self, root: tk.Tk):
        """Initialize the main window and default styles."""
        self.root = root
        self.default_font = tkFont.nametofont("TkDefaultFont").actual()
        self.setup_ui()

    def setup_ui(self):
        """Configure window size, layout, and add main UI components"""
        self.root.title("msaGUI")
        width = 800
        height = 500
        screenwidth = self.root.winfo_screenwidth()
        screenheight = self.root.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        self.root.geometry(alignstr)
        self.root.resizable(True, True)
        self.root.configure(bg=ViewDefaults.bg)

        for i in (3,5):
            self.root.rowconfigure(i, weight=16)
            self.root.columnconfigure(i, weight=16)
        self.root.rowconfigure(14, weight=1)
        self.build_widgets()
        # self.build_wavenumber_inputs()
        self.build_menubar()
        self.widgets = [self.buttons, self.labels, self.listbox, self.display]

    def build_paned_window(self) -> tk.PanedWindow:
        """Create and place the main paned window."""
        paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned_window.grid(row=0, column=0, rowspan=7, columnspan=16, sticky="nsew", padx=2, pady=2)  # Fill the entire window
        return paned_window

    def build_widgets(self):
        self.paned_window = self.build_paned_window()
        self.listbox = ListboxView(self.paned_window)
        

        button_details = {"Add": dict(row=7, column=0, rowspan=1, columnspan=1, sticky="nsew", padx=2),
                "Delete": dict(row=8, column=0, rowspan=1, columnspan=1, sticky="nsew", padx=2),
                "Analyze": dict(row=9, column=0, rowspan=1, columnspan=2, sticky="nsew", padx=2),
                "Set-Up": dict(row=7, column=1, rowspan=1, columnspan=1, sticky="nsew", padx=2),
                # "Groups": dict(row=8, column=1, rowspan=1, columnspan=1, sticky="nsew", padx=2),
                "Export": dict(row=8, column=1, rowspan=1, columnspan=1, sticky="nsew", padx=2)}
        
        self.buttons = WidgetsView(self.root, button_details, tk.Button) # pyright: ignore[reportArgumentType]
        
        label_details = {"Filename": dict(row=7, column=2, rowspan=1, columnspan=4, sticky="nsew", padx=2),
                         "Statistics": dict(row=8, column=2, rowspan=2, columnspan=4, sticky="nsew", padx=2)}
        self.labels = WidgetsView(self.root, label_details, tk.Label) # pyright: ignore[reportArgumentType]

        self.display = DisplayView(self.paned_window, self.root, self.labels.items['Filename'])

    def build_menubar(self):
        """Build the menu bar and menus for file/view/path options."""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        self.initialize_menu_vars()

        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_separator()

        self.export_menu = tk.Menu(self.file_menu, tearoff=0)
        self.file_menu.add_cascade(label="Export", menu=self.export_menu)
        self.export_menu.add_command(label="File List")
        self.export_menu.add_command(label="Settings")
        self.export_menu.add_command(label="Default Settings")
        self.export_menu.add_command(label="Logs")

        self.import_menu = tk.Menu(self.file_menu, tearoff=0)
        self.file_menu.add_cascade(label="Import", menu=self.import_menu)
        self.import_menu.add_command(label="File List")
        self.import_menu.add_command(label="Settings")

        self.config_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Config", menu=self.config_menu)
        self.config_menu.add_command(label="General")
        self.config_menu.add_separator()
        self.config_menu.add_command(label="Image")
        self.config_menu.add_command(label="Histogram")

        self.view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="View", menu=self.view_menu)
        labels = ("Group View", "Histograms")
        variables = (self.show_groups, self.show_histograms)
        for label, variable in zip(labels, variables):
            self.view_menu.add_checkbutton(label=label, onvalue=1, offvalue=0,
                                           variable=variable)

        self.show_menu = tk.Menu(self.view_menu, tearoff=0)
        self.view_menu.add_cascade(label="Show", menu=self.show_menu)
        self.show_menu.add_checkbutton(label="Inputs", onvalue=1, offvalue=0,
                           variable=self.show_inputs)
        self.show_menu.add_checkbutton(label="Outputs", onvalue=1, offvalue=0,
                           variable=self.show_outputs)

        self.fpath_menu = tk.Menu(self.view_menu, tearoff=0)
        self.view_menu.add_cascade(label="File Path", menu=self.fpath_menu)
        self.fpath_menu.add_radiobutton(label="View Full Path", variable=self.view_mode, value="full")
        self.fpath_menu.add_radiobutton(label="View Parent", variable=self.view_mode, value="parent")
        self.fpath_menu.add_radiobutton(label="View File Only", variable=self.view_mode, value="file")

        self.sort_menu = tk.Menu(self.view_menu, tearoff=0)
        self.view_menu.add_cascade(label="Sort", menu=self.sort_menu)
        self.sort_menu.add_radiobutton(label="Time Imported", variable=self.sort_key, value="time_imported")
        self.sort_menu.add_radiobutton(label="Basename", variable=self.sort_key, value="basename")
        self.sort_menu.add_radiobutton(label="Parent Path", variable=self.sort_key, value="parent_path")
        self.sort_menu.add_radiobutton(label="Group", variable=self.sort_key, value="group")
        self.sort_menu.add_radiobutton(label="Keyword", variable=self.sort_key, value="keyword")
        self.sort_menu.add_separator()
        self.sort_menu.add_checkbutton(label="Descending", onvalue=1, offvalue=0,
                           variable=self.sort_desc)
        return

    def initialize_menu_vars(self):
        """Initialize Tkinter variables for menu state."""
        self.show_groups = tk.BooleanVar()
        self.show_histograms = tk.BooleanVar()
        self.show_inputs = tk.BooleanVar(value=True)
        self.show_outputs = tk.BooleanVar(value=True)
        self.view_mode = tk.StringVar(value="full")
        self.sort_key = tk.StringVar(value="time_imported")
        self.sort_desc = tk.BooleanVar(value=False)
        return
    
    def show_error(self, errors: dict):
        """Show error dialog for failed file additions."""
        error_str = "Could not add/delete the following files:\n"
        for error in errors:
            error_str += str(error) + "\n"
        messagebox.showerror("Error", error_str)
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
            "show_inputs": self.show_inputs.get(),
            "show_outputs": self.show_outputs.get(),
            "view_mode": self.view_mode.get()
        }
        return settings
    
    def get_widget(self, widget_name: str) -> tk.Widget:
        """Get a reference to a specific widget by name."""
        for widget in self.widgets:
            if widget_name in widget.items:
                return widget
        raise ValueError(f"Widget '{widget_name}' not found.")