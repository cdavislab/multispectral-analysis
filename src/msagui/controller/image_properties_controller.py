from msagui.model.msa_utils import is_number
from msagui.view.image_properties_view import PropertiesView, ImagePropertiesView

# ---------------------------------------------------------------------------
# Schemas
# Each item is a dict describing one UI row.  The view renders them generically
# — adding a new setting only requires adding an entry here.
#
# Supported kinds:
#   "section"      – bold heading;  keys: label
#   "entry"        – text entry;    keys: key, label, hint
#   "checkbutton"  – checkbox;      keys: key, label, hint
#   "double"       – two side-by-side widgets on one row;
#                    keys: label, hint, widget ("entry"|"checkbutton"),
#                          fields (list of {key, sublabel})
#
# All keys must correspond to attributes on ImagingSettings.
# ---------------------------------------------------------------------------

PREFS_SCHEMA = [
    {"kind": "section", "label": "Export"},
    {"kind": "entry",       "key": "export_directory", "label": "Export Directory",
     "hint": "Folder path for saved exports (e.g. /path/to/output or 'folder' for same folder as input)"},
    {"kind": "entry",       "key": "format",           "label": "File Format",
     "hint": "Image format override (e.g. png, jpg, tiff); leave blank to infer from filename"},
    {"kind": "entry",       "key": "dpi",              "label": "DPI",
     "hint": "Resolution for saved images (dots per inch)"},
    {"kind": "checkbutton", "key": "transparent",      "label": "Transparent Background",
     "hint": "Save image with a transparent background (PNG only)"},
    {"kind": "section", "label": "Figure Padding"},
    {"kind": "entry",       "key": "bbox_inches",      "label": "Bounding Box",
     "hint": "Bounding box setting for saved figure (e.g. 'tight')"},
    {"kind": "entry",       "key": "pad_inches",       "label": "Padding (inches)",
     "hint": "Padding around the figure when bbox_inches is 'tight'"},
    {"kind": "section", "label": "Colours"},
    {"kind": "entry",       "key": "facecolor",        "label": "Face Colour",
     "hint": "Background colour of the figure (e.g. 'white', 'auto')"},
    {"kind": "entry",       "key": "edgecolor",        "label": "Edge Colour",
     "hint": "Edge colour of the figure (e.g. 'black', 'auto')"},
    {"kind": "section", "label": "Backend"},
    {"kind": "entry",       "key": "backend",          "label": "Matplotlib Backend",
     "hint": "Matplotlib rendering backend override; leave blank for default"},
]

IMG_PREFS_SCHEMA = [
    {"kind": "section", "label": "Font"},
    {"kind": "entry", "key": "font",        "label": "Font",        "hint": "Font family for axes text (e.g. DejaVu Sans)"},
    {"kind": "entry", "key": "font_size",   "label": "Font Size",   "hint": "Font size of axes text in points"},
    {"kind": "entry", "key": "font_weight", "label": "Font Weight", "hint": "(e.g. light, normal, heavy, bold)"},
    {"kind": "section", "label": "Color Map"},
    {"kind": "entry", "key": "cmap",        "label": "Color Map",   "hint": "Matplotlib colormap name (e.g. viridis, gray); leave blank for default"},
    {"kind": "double", "label": "Color Scale", "hint": "Minimum and maximum values of the colorbar", "widget": "entry",
     "fields": [{"key": "vmin", "sublabel": "Min"}, {"key": "vmax", "sublabel": "Max"}]},
    {"kind": "entry", "key": "cunits",      "label": "Units",       "hint": "Units label for the colorbar"},
    {"kind": "checkbutton", "key": "show_colorbar", "label": "Show Colorbar",
     "hint": "Show a colorbar next to each image"},
    {"kind": "section", "label": "Image Display"},
    {"kind": "entry", "key": "interpolation", "label": "Interpolation", "hint": "Pixel interpolation method (e.g. nearest, bilinear); leave blank for default"},
    {"kind": "entry", "key": "origin",       "label": "Origin",        "hint": "Image origin: 'upper' or 'lower'"},
    {"kind": "entry", "key": "aspect",       "label": "Aspect",        "hint": "Axes aspect ratio (e.g. 'auto', 'equal')"},
    {"kind": "section", "label": "Scale Bar"},
    {"kind": "entry", "key": "pixel_scale",          "label": "Pixel Scale",          "hint": "Physical size of one pixel (in scale bar units)"},
    {"kind": "entry", "key": "scale_bar_units",      "label": "Scale Bar Units",      "hint": "Units label for the scale bar (e.g. micrometer)"},
    {"kind": "entry", "key": "scale_bar_location",   "label": "Scale Bar Location",   "hint": "Position of the scale bar (e.g. lower right)"},
    {"kind": "entry", "key": "scale_bar_fixed_value","label": "Scale Bar Fixed Value","hint": "Fixed length for the scale bar in scale bar units; 0 to disable, blank for auto"},
    {"kind": "section", "label": "Extra"},
    {"kind": "entry", "key": "num_ticks",   "label": "Number of Tick Marks", "hint": "Number of axis tick marks (0 = no ticks)"},
]

# ---------------------------------------------------------------------------
# Type coercion
# ImagingSettings uses specific Python types; Entry widgets return plain strings
# and checkbuttons return bool.  This map specifies any non-str coercion needed.
#
# "int"           → int(value)
# "float"         → float(value)
# "float_or_none" → None if value is empty, else float(value)
# "str_or_none"   → None if value is empty, else str(value)
# ---------------------------------------------------------------------------

_COERCE_MAP: dict[str, str] = {
    "dpi":                   "int",
    "pad_inches":            "float",
    "font_size":             "float",
    "pixel_scale":           "float",
    "num_ticks":             "int",
    "vmin":                  "float_or_none",
    "vmax":                  "float_or_none",
    "scale_bar_fixed_value": "float_or_none",
    "cmap":                  "str_or_none",
    "interpolation":         "str_or_none",
    "format":                "str_or_none",
    "facecolor":             "str_or_none",
    "edgecolor":             "str_or_none",
    "backend":               "str_or_none",
    "export_directory":      "str_or_none",
}


def _coerce(key: str, value):
    """Apply the coercion rule for *key* to *value*."""
    rule = _COERCE_MAP.get(key)
    if rule is None:
        return value  # bool from BooleanVar or plain str — no conversion needed
    if rule == "int":
        return int(value) if value != "" else 0
    if rule == "float":
        return float(value) if value != "" else 0.0
    if rule == "float_or_none":
        return None if value == "" else float(value)
    if rule == "str_or_none":
        return None if value == "" else str(value)
    return value


class ImagePropertiesController:
    def __init__(self, model, view):
        self.model = model
        self.view = view

    def preferences(self):
        """Open the general (export) preferences dialog."""
        values = self.model.settings.to_dict()
        self.properties = PropertiesView(self.view.root, PREFS_SCHEMA, values)
        self.properties.save_button.config(command=self.pref_save_and_quit)

    def pref_save_and_quit(self):
        """Write general preferences back to ImagingSettings and close the dialog."""
        coerced = {k: _coerce(k, v) for k, v in self.properties.get_settings().items()}
        self.model.settings.update_from_dict(coerced)
        self.properties.pref_window.destroy()

    def image_preferences(self):
        """Open the image display preferences dialog."""
        values = self.model.settings.to_dict()
        self.image_properties = ImagePropertiesView(self.view.root, IMG_PREFS_SCHEMA, values)
        self.image_properties.save_button.config(command=self.image_pref_save_and_quit)

    def image_pref_save_and_quit(self):
        """Write image preferences back to ImagingSettings and close the dialog."""
        coerced = {k: _coerce(k, v) for k, v in self.image_properties.get_settings().items()}
        self.model.settings.update_from_dict(coerced)
        self.image_properties.pref_window.destroy()

    def save_string_pref(self, key, value):
        self.model.settings.update_from_dict({key: value})

    def save_float_pref(self, key, value):
        if is_number(value):
            self.model.settings.update_from_dict({key: float(value)})
        else:
            print(f"Invalid value for {key}: {value}")