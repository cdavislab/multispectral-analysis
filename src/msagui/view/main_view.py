import tkinter as tk
import tkinter.font as tkFont
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

        self.make_buttons()
        self.make_labels()
        # self.build_wavenumber_inputs()
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
        self.file_list = self.decorate(tk.Listbox(frm, xscrollcommand=scrollbar.set, selectmode=tk.MULTIPLE))
        self.file_list.configure(fg="#333333", borderwidth="1px")
        self.file_list.pack(expand=True, fill=tk.BOTH)
        scrollbar.config(command=self.file_list.xview)
        root.add(frm)
        return
    
    def build_image_viewer(self, root):
        """Build the image display panel."""
        self.img_panel = tk.Label(root, bg='gray')
        self.panel_img = ""
        root.add(self.img_panel)
        return
    
    def create_widget(self, widget_class, grid, **kwargs):
        widget = widget_class(self.root, **kwargs)
        """Apply default styling to widgets."""
        widget.configure(
            bg=self.DEFAULT_BG,
            fg=self.DEFAULT_FG,
            justify="center",
            font=(self.DEFAULT_FONT_FAMILY, self.DEFAULT_FONT_SIZE)
        )
        widget.grid(**grid)
        return widget
    
    def make_labels(self):
        label_details = {"Filename": dict(row=7, column=2, rowspan=1, columnspan=4, sticky="nsew", padx=2),
                         "Statistics": dict(row=8, column=2, rowspan=2, columnspan=4, sticky="nsew", padx=2)}
        self.labels = dict()
        for text, grid_options in label_details.items():
            self.labels[text] = self.create_widget(tk.Label, grid_options, text=text, relief='groove')

    def make_buttons(self):
        button_details = {"Add": dict(row=7, column=0, rowspan=1, columnspan=1, sticky="nsew", padx=2),
                "Delete": dict(row=8, column=0, rowspan=1, columnspan=1, sticky="nsew", padx=2),
                "Analyze": dict(row=9, column=0, rowspan=1, columnspan=1, sticky="nsew", padx=2),
                "Frequency": dict(row=7, column=1, rowspan=2, columnspan=1, sticky="nsew", padx=2),
                "Export Folder": dict(row=9, column=1, rowspan=1, columnspan=1, sticky="nsew", padx=2)}
        
        self.buttons = dict()
        for text, grid_options in button_details.items():
            self.buttons[text] = self.create_widget(tk.Button, grid_options, text=text, relief="raised")

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

    def display(self, img):
        """Display an image in the image panel, resizing as needed."""
        screen_width, screen_height = self.get_shape(self.root)
        sash_position = self.paned_window.sash_coord(0)[0]
        img_width = screen_width - sash_position

        bottom_menu_height = self.labels['Filename'].winfo_height()*7
        img_height = screen_height - bottom_menu_height

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
    
    def set_button_text(self, button_name: str, text: str):
        self.buttons[button_name] = text

    def get_selected_indices(self) -> list[int]:
        """Get indices of selected files in the listbox."""
        print("Selected indices:", self.file_list.curselection())
        return list(self.file_list.curselection())