import tkinter as tk
from tkinter import ttk


HINT_TEXT_COLOR = "#9A9A9A"


class PropertiesView:
    """Generic schema-driven dialog for editing settings.

    Parameters
    ----------
    root : tk.Widget
        Parent window.
    schema : list[dict]
        Ordered list of field descriptors.  Each dict must have a ``"kind"``
        key; supported kinds are:

        ``"section"``
            Bold section heading.  Required key: ``"label"``.

        ``"entry"`` / ``"checkbutton"``
            Single row with a label, an entry or checkbox widget, and a grey
            hint.  Required keys: ``"key"`` (model attribute name), ``"label"``,
            ``"hint"``.

        ``"double"``
            Two side-by-side widgets sharing one row.  Required keys:
            ``"label"``, ``"hint"``, ``"widget"`` (``"entry"`` or
            ``"checkbutton"``), ``"fields"`` (list of dicts with ``"key"`` and
            ``"sublabel"``).

    values : dict
        Current values keyed by the same ``"key"`` strings used in *schema*.
        Missing keys default to ``""`` / ``False``.
    """

    def __init__(self, root, schema, values, max_height: int = 500, min_width: int = 560):
        self.pref_window = tk.Toplevel(root)
        self._root = root
        self.pref_window.title("Preferences")

        # --- scrollable container -------------------------------------------
        # Canvas + scrollbar live directly in the Toplevel.
        # pref_frame is a plain Frame created *inside* the canvas so all
        # widget helpers work exactly as before.
        self._canvas = tk.Canvas(self.pref_window, highlightthickness=0)
        self._scrollbar = ttk.Scrollbar(
            self.pref_window, orient="vertical", command=self._canvas.yview
        )
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self.pref_frame = tk.Frame(self._canvas)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self.pref_frame, anchor="nw"
        )

        # Resize the scroll region whenever the inner frame changes size.
        self.pref_frame.bind("<Configure>", self._on_frame_configure)
        # Keep the inner frame as wide as the canvas.
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        # Mousewheel scrolling.
        self._canvas.bind_all("<MouseWheel>",   self._on_mousewheel)        # Windows / macOS
        self._canvas.bind_all("<Button-4>",     self._on_mousewheel)        # Linux scroll up
        self._canvas.bind_all("<Button-5>",     self._on_mousewheel)        # Linux scroll down
        # Stop capturing mousewheel when this window closes.
        self.pref_window.bind("<Destroy>", lambda _: self._unbind_mousewheel())
        # --------------------------------------------------------------------

        self.padx_label = (20, 0)
        self.padx_entry = (0, 20)
        self.padx_hint  = (20, 20)
        self.row = 0
        # key (schema "key") -> {"entry": tk.Entry | tk.BooleanVar, ...}
        self.properties = {}

        self._create_widgets(schema, values)

        self.save_button = tk.Button(self.pref_frame, text="Save")
        self.save_button.grid(row=self.row, column=4, columnspan=1, pady=(10, 5))

        self.pref_frame.grid_columnconfigure(0, weight=3)
        for i in range(1, 5):
            self.pref_frame.grid_columnconfigure(i, weight=1)

        # Cap the initial window height so it doesn't grow off-screen;
        # enforce a minimum width so all labels and entries fit comfortably.
        self.pref_window.update_idletasks()
        content_h = self.pref_frame.winfo_reqheight()
        content_w = self.pref_frame.winfo_reqwidth()
        win_h = min(content_h, max_height)
        win_w = max(content_w, min_width)
        self._canvas.configure(height=win_h, width=win_w)
        self.pref_window.minsize(win_w + 20, 200)  # +20 for the scrollbar
        self._position_window(win_w + 20, win_h)

    # ------------------------------------------------------------------
    # Scroll helpers
    # ------------------------------------------------------------------

    def _position_window(self, width: int, height: int):
        """Place the dialog centered over the parent and clamp to screen bounds."""
        self.pref_window.update_idletasks()

        parent_x = self._root.winfo_rootx()
        parent_y = self._root.winfo_rooty()
        parent_w = self._root.winfo_width()
        parent_h = self._root.winfo_height()

        screen_w = self.pref_window.winfo_screenwidth()
        screen_h = self.pref_window.winfo_screenheight()

        x = parent_x + max(0, (parent_w - width) // 2)
        y = parent_y + max(0, (parent_h - height) // 2)

        x = max(0, min(x, screen_w - width))
        y = max(0, min(y, screen_h - height))

        self.pref_window.geometry(f"{width}x{height}+{x}+{y}")

    def _on_frame_configure(self, _event=None):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        # Only scroll if this window is in focus.
        if not self.pref_window.winfo_exists():
            return
        if event.num == 4:          # Linux up
            self._canvas.yview_scroll(-1, "units")
        elif event.num == 5:        # Linux down
            self._canvas.yview_scroll(1, "units")
        else:                       # Windows / macOS
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _unbind_mousewheel(self):
        try:
            self._canvas.unbind_all("<MouseWheel>")
            self._canvas.unbind_all("<Button-4>")
            self._canvas.unbind_all("<Button-5>")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Schema rendering
    # ------------------------------------------------------------------

    def _create_widgets(self, schema, values):
        """Iterate *schema* and render each field using the helpers below."""
        for item in schema:
            kind = item["kind"]
            if kind == "section":
                self.make_label(item["label"])

            elif kind == "entry":
                raw = values.get(item["key"])
                self.make_form(
                    item["key"], item["label"], item["hint"],
                    "entry", "" if raw is None else str(raw),
                )

            elif kind == "checkbutton":
                var = tk.BooleanVar(value=bool(values.get(item["key"], False)))
                self.make_form(
                    item["key"], item["label"], item["hint"],
                    "checkbutton", var,
                )

            elif kind == "double":
                fields_data = []
                for field in item["fields"]:
                    if item["widget"] == "checkbutton":
                        var = tk.BooleanVar(value=bool(values.get(field["key"], False)))
                        fields_data.append((field["key"], field["sublabel"], var))
                    else:
                        raw = values.get(field["key"])
                        fields_data.append(
                            (field["key"], field["sublabel"],
                             "" if raw is None else str(raw))
                        )
                self.make_double_form(
                    item["label"], item["hint"], item["widget"], fields_data
                )

    # ------------------------------------------------------------------
    # Widget helpers
    # ------------------------------------------------------------------

    def make_label(self, text):
        """Render a bold section heading."""
        label = tk.Label(self.pref_frame, text=text, font=("Verdana", 10, "bold"))
        label.grid(row=self.row, column=0, columnspan=1, sticky='w', padx=self.padx_label)
        self.row += 1

    def make_separator(self):
        """Render a horizontal separator line."""
        separator = ttk.Separator(self.pref_frame, orient='horizontal')
        separator.grid(row=self.row, column=0, columnspan=5, sticky='ew')
        self.row += 1

    def make_form(self, key, title, hint, type_of_entry, variable):
        """Render a single-row form field and register it under *key*."""
        label = tk.Label(self.pref_frame, text=title)
        label.grid(row=self.row, column=0, sticky='w', padx=self.padx_label)
        if type_of_entry == "entry":
            entry = tk.Entry(self.pref_frame)
            entry.insert(0, variable)
            entry.grid(row=self.row, column=1, columnspan=4, sticky='we', padx=self.padx_entry)
        elif type_of_entry == "checkbutton":
            entry = variable  # tk.BooleanVar
            checkbox = tk.Checkbutton(self.pref_frame, variable=entry)
            checkbox.grid(row=self.row, column=1, columnspan=4, sticky='w', padx=self.padx_entry)
        label_hint = tk.Label(self.pref_frame, text=hint, fg=HINT_TEXT_COLOR)
        label_hint.grid(row=self.row + 1, column=0, columnspan=5, sticky='w', padx=self.padx_hint)
        self.properties[key] = {"label": label, "entry": entry, "label_hint": label_hint}
        self.row += 2

    def make_double_form(self, title, hint, type_of_entry, fields):
        """Render two side-by-side widgets on one row.

        Parameters
        ----------
        fields : list of (key, sublabel, variable)
        """
        label = tk.Label(self.pref_frame, text=title)
        label.grid(row=self.row, column=0, sticky='w', padx=self.padx_label)
        label_hint = tk.Label(self.pref_frame, text=hint, fg=HINT_TEXT_COLOR)
        label_hint.grid(row=self.row + 1, column=0, columnspan=5, sticky='w', padx=self.padx_hint)
        column_num = 1
        for key, sublabel, variable in fields:
            sublabel_widget = tk.Label(self.pref_frame, text=sublabel)
            sublabel_widget.grid(row=self.row, column=column_num, sticky='w')
            column_num += 1
            if type_of_entry == "entry":
                entry = tk.Entry(self.pref_frame, width=5)
                entry.insert(0, variable)
                entry.grid(row=self.row, column=column_num, columnspan=1, sticky='w', padx=self.padx_entry)
            elif type_of_entry == "checkbutton":
                entry = variable  # tk.BooleanVar
                checkbox = tk.Checkbutton(self.pref_frame, variable=entry)
                checkbox.grid(row=self.row, column=column_num, columnspan=1, sticky='w', padx=0)
            column_num += 1
            self.properties[key] = {"label": sublabel_widget, "entry": entry, "label_hint": label_hint}
        self.row += 2

    # ------------------------------------------------------------------
    # Value accessors
    # ------------------------------------------------------------------

    def get_settings(self):
        """Return ``{key: value}`` for every registered field.

        Values are plain Python objects: ``str`` for Entry widgets,
        ``bool`` for BooleanVar widgets.
        """
        return {key: props["entry"].get() for key, props in self.properties.items()}

    def get_setting(self, key):
        """Return the current value for a single field *key*."""
        return self.properties[key]["entry"].get()

    def get_setting_keys(self):
        """Return all registered field keys."""
        return self.properties.keys()


class ImagePropertiesView(PropertiesView):
    """Dialog for editing image preferences (title override only)."""

    def __init__(self, root, schema, values, max_height: int = 500, min_width: int = 560):
        super().__init__(root, schema, values, max_height=max_height, min_width=min_width)
        self.pref_window.title("Image Preferences")