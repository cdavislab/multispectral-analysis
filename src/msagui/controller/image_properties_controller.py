import logging
from typing import Any
import tkinter.messagebox as messagebox

from msagui.model.msa_utils import is_number
from msagui.view.image_properties_view import PropertiesView, ImagePropertiesView
from msagui.controller.settings_validation import (
    coerce_with_validation,
    format_invalid_values_message,
)

logger = logging.getLogger(__name__)

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
    {"kind": "entry",       "key": "export_format",    "label": "Export File Type",
     "hint": "File format for the Export button (e.g. png, tif, jpg)"},
    {"kind": "entry",       "key": "dpi",              "label": "DPI",
     "hint": "Resolution for saved images (dots per inch)"},
    {"kind": "checkbutton", "key": "transparent",      "label": "Transparent Background",
     "hint": "Save image with a transparent background (PNG only)"},
    {"kind": "section", "label": "Figure Padding"},
    {"kind": "entry",       "key": "pad_inches",       "label": "Padding (inches)",
     "hint": "Padding around the figure when bbox_inches is 'tight'"},
    {"kind": "section", "label": "Colors"},
    {"kind": "entry",       "key": "facecolor",        "label": "Face Color",
     "hint": "Background color of the figure (e.g. 'white', 'auto')"},
    {"kind": "entry",       "key": "edgecolor",        "label": "Edge Color",
     "hint": "Edge color of the figure (e.g. 'black', 'auto')"},
]

IMG_PREFS_SCHEMA = [
    {"kind": "section", "label": "Font"},
    {"kind": "entry", "key": "font",        "label": "Font",        "hint": "Font family for axes text (e.g. DejaVu Sans)"},
    {"kind": "entry", "key": "font_size",   "label": "Font Size",   "hint": "Font size of axes text in points"},
    {"kind": "entry", "key": "font_weight", "label": "Font Weight", "hint": "(e.g. light, normal, heavy, bold)"},
    {"kind": "section", "label": "Color Map"},
    {"kind": "entry", "key": "cmap",        "label": "Color Map",   "hint": "Matplotlib colormap name (e.g. viridis, gray); leave blank for default"},
    {"kind": "entry", "key": "bad",         "label": "Bad Value Color", "hint": "Color for NaN/masked pixels (e.g. black, magenta, #000000); leave blank to use colormap default"},
    {"kind": "double", "label": "Color Scale", "hint": "Minimum and maximum values of the colorbar", "widget": "entry",
     "fields": [{"key": "vmin", "sublabel": "Min"}, {"key": "vmax", "sublabel": "Max"}]},
    {"kind": "entry", "key": "cunits",      "label": "Units",       "hint": "Units label for the colorbar"},
    {"kind": "checkbutton", "key": "show_colorbar", "label": "Show Colorbar",
     "hint": "Show a colorbar next to each image"},
    {"kind": "section", "label": "Image Display"},
    {"kind": "entry", "key": "interpolation", "label": "Interpolation", "hint": "Pixel interpolation method (e.g. nearest, bilinear); leave blank for default"},
    {"kind": "entry", "key": "origin",       "label": "Origin",        "hint": "Image origin: 'upper' or 'lower'"},
    {"kind": "section", "label": "Scale Bar"},
    {"kind": "entry", "key": "pixel_scale",          "label": "Pixel Scale",          "hint": "Physical size of one pixel (in scale bar units)"},
    {"kind": "entry", "key": "scale_bar_units",      "label": "Scale Bar Units",      "hint": "Units label for the scale bar (e.g. micrometer)"},
    {"kind": "entry", "key": "scale_bar_color",      "label": "Scale Bar Color",      "hint": "Color of the scale bar and its label (e.g. white, black, #FFFFFF)"},
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
    "bad":                   "str_or_none",
    "interpolation":         "str_or_none",
    "scale_bar_color":       "str_or_none",
    "facecolor":             "str_or_none",
    "edgecolor":             "str_or_none",
}

class ImagePropertiesController:
    def __init__(self, model: Any, view: Any) -> None:
        self.model = model
        self.view = view

    def preferences(self) -> None:
        """Open the general (export) preferences dialog."""
        values = self.model.settings.to_dict()
        self.properties = PropertiesView(self.view.root, PREFS_SCHEMA, values)
        self.properties.save_button.config(command=self.pref_save_and_quit)

    def pref_save_and_quit(self) -> None:
        """Write general preferences back to ImagingSettings and close the dialog."""
        raw_settings = self.properties.get_settings()
        coerced, invalid = coerce_with_validation(raw_settings, _COERCE_MAP)
        if invalid:
            messagebox.showerror(
                "Invalid Settings",
                format_invalid_values_message(PREFS_SCHEMA, invalid),
                parent=self.properties.pref_window,
            )
            return
        self.model.settings.update_from_dict(coerced)
        self.properties.pref_window.destroy()

    def image_preferences(self) -> None:
        """Open the image display preferences dialog."""
        values = self.model.settings.to_dict()
        self.image_properties = ImagePropertiesView(self.view.root, IMG_PREFS_SCHEMA, values)
        self.image_properties.save_button.config(command=self.image_pref_save_and_quit)

    def image_pref_save_and_quit(self) -> None:
        """Write image preferences back to ImagingSettings and close the dialog."""
        raw_settings = self.image_properties.get_settings()
        coerced, invalid = coerce_with_validation(raw_settings, _COERCE_MAP)
        if invalid:
            messagebox.showerror(
                "Invalid Image Properties",
                format_invalid_values_message(IMG_PREFS_SCHEMA, invalid),
                parent=self.image_properties.pref_window,
            )
            return
        self.model.settings.update_from_dict(coerced)
        self.image_properties.pref_window.destroy()

    def save_string_pref(self, key: str, value: Any) -> None:
        """Persist a string-like preference value on the model settings."""
        self.model.settings.update_from_dict({key: value})

    def save_float_pref(self, key: str, value: Any) -> None:
        """Persist numeric preference value after validating parseability."""
        if is_number(value):
            self.model.settings.update_from_dict({key: float(value)})
        else:
            logger.warning("Invalid value for %s: %r", key, value)