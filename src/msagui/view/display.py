import tkinter as tk
from PIL import ImageTk
import logging
from typing import Any
from PIL.Image import Image
from msagui.view.defaults import ViewDefaults

logger = logging.getLogger(__name__)

class View:
    def __init__(self) -> None:
        pass

    def decorate(self, widget: tk.Widget) -> tk.Widget:
        """Apply default styling to widgets."""
        widget.configure(
            bg=ViewDefaults.bg, # pyright: ignore[reportCallIssue]
            fg=ViewDefaults.fg, # pyright: ignore[reportCallIssue]
            justify=ViewDefaults.justify, # pyright: ignore[reportCallIssue]
            font=(ViewDefaults.font_family, ViewDefaults.font_size) # pyright: ignore[reportCallIssue]
        )
        return widget

    def build(self, root: Any) -> None:
        """Build the view components. To be implemented by subclasses."""
        pass

    def update(self, *args: Any, **kwargs: Any) -> None:
        """Update the view components. To be implemented by subclasses."""
        pass

class DisplayView(View):
    def __init__(self, panel: tk.PanedWindow, root: tk.Widget, widget_below: tk.Widget) -> None:
        """Initialize the display view within the main application window."""
        self.build(panel)
        self.panel = panel
        self.root = root
        self.widget_below = widget_below
        self.items = {"img_panel": self.img_panel}

    def build(self, root: tk.PanedWindow) -> None:
        """Build the image display panel."""
        self.img_panel = self.decorate(tk.Label(root, bg='gray'))
        self.panel_img: ImageTk.PhotoImage | None = None
        root.add(self.img_panel)
        return
    
    def get_shape(self, widget: tk.Widget) -> tuple[int, int]:
        """Utility: get widget width and height."""
        geometry = widget.winfo_geometry()  # Get the geometry string
        # Split the string to extract the width and height
        width, height = geometry.split('x')[0], geometry.split('x')[1].split('+')[0]
        return int(width), int(height)

    def resize(self, img: Image) -> Image:
        """Display an image in the image panel, resizing as needed."""
        screen_width, screen_height = self.get_shape(self.root)
        sash_position = self.panel.sash_coord(0)[0]
        img_width = screen_width - sash_position

        bottom_menu_height = self.widget_below.winfo_height()*7
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
        return img

    def update(self, img: Image) -> None:
        """Render the provided image in the panel after resizing."""
        img = self.resize(img)
        self.panel_img = ImageTk.PhotoImage(img)
        self.img_panel.configure(image=self.panel_img) # pyright: ignore[reportCallIssue]
        return

class ListboxView(View):
    def __init__(self, root: tk.PanedWindow) -> None:
        """Initialize the file list view within the main application window."""
        self.root = root
        self.build(self.root)
        self.items = {"listbox": self.file_list}
        
    def update(self, files: list[str]) -> None:
        """Update the listbox with a new list of files."""
        self.file_list.delete(0, tk.END)
        for name in files:
            # logger.info(f"Adding file to listbox: {name}")
            self.file_list.insert(tk.END, name)
            
    def build(self, paned_window: tk.PanedWindow) -> None:
        """Build the file list viewer with scrollbar."""
        frm = tk.Frame(paned_window)
        self.scrollbar = tk.Scrollbar(frm, orient="horizontal")
        self.scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.file_list: tk.Listbox = self.decorate(
            tk.Listbox(frm, xscrollcommand=self.scrollbar.set, selectmode=tk.MULTIPLE)) # pyright: ignore[reportAttributeAccessIssue]
        self.file_list.configure(fg="#121212", borderwidth="1px")
        self.file_list.pack(expand=True, fill=tk.BOTH)
        self.scrollbar.config(command=self.file_list.xview)
        paned_window.add(frm)
        return
    
    def get_selected_indices(self) -> list[int]:
        """Get indices of selected files in the listbox."""
        selected = list(self.file_list.curselection())
        logger.debug("Selected indices: %s", selected)
        return selected

class WidgetsView(View):
    def __init__(self, root: tk.Widget, widgets: dict[str, dict[str, Any]], widget_type: type[tk.Widget]) -> None:
        """Initialize the labels view within the main application window."""
        self.build(root, widgets, widget_type)

    def create_widget(
        self,
        root: tk.Widget,
        widget_class: type[tk.Widget],
        grid: dict[str, Any],
        **kwargs: Any,
    ) -> tk.Widget:
        """Create, decorate, and grid a widget instance."""
        widget = widget_class(root, **kwargs)
        widget = self.decorate(widget)
        widget.grid(**grid)
        return widget
    
    def build(self, root: tk.Widget, widgets: dict[str, dict[str, Any]], widget_type: type[tk.Widget]) -> None:
        """Build and register labeled widget instances from configuration."""
        self.items: dict[str, tk.Widget] = dict()
        for text, grid_options in widgets.items():
            self.items[text] = self.create_widget(root, widget_type, grid_options, text=text, relief='groove')
        return
    
    def update(self, text: str, new_value: str) -> None:
        """Update the text of a specific widget."""
        if text in self.items:
            self.items[text].configure(text=new_value)
        else:
            raise ValueError(f"Widget with text '{text}' not found.")