"""Controller and schema for the Histogram Settings dialog."""

from typing import Any
import tkinter.messagebox as messagebox

from msagui.view.image_properties_view import PropertiesView
from msagui.controller.settings_validation import (
    coerce_with_validation,
    format_invalid_values_message,
)

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

HIST_SCHEMA = [
    {"kind": "section", "label": "Data"},
    {"kind": "entry",       "key": "bins",           "label": "Bins",
     "hint": "Number of histogram bins (integer, e.g. 50)"},
    {"kind": "checkbutton", "key": "exclude_zeros",  "label": "Exclude Zeros",
     "hint": "Omit zero-valued pixels from the histogram (recommended for thresholded images)"},

    {"kind": "section", "label": "Appearance"},
    {"kind": "entry",       "key": "color",          "label": "Bar Color",
     "hint": "Matplotlib color name or hex code for histogram bars (e.g. steelblue, #4a90d9)"},
    {"kind": "checkbutton", "key": "kde",            "label": "Show KDE Curve",
     "hint": "Overlay a kernel density estimate curve on the histogram"},
    {"kind": "entry",       "key": "kde_color",      "label": "KDE Color",
     "hint": "Color for the KDE line (e.g. navy); only used when Show KDE Curve is enabled"},
    {"kind": "checkbutton", "key": "log_scale",      "label": "Log Scale (Y-axis)",
     "hint": "Use a logarithmic scale for the count axis"},
    {"kind": "checkbutton", "key": "grid",           "label": "Show Grid",
     "hint": "Display a light background grid"},

    {"kind": "section", "label": "Axis"},
    {"kind": "entry",       "key": "xlabel",         "label": "X-axis Label",
     "hint": "Label for the horizontal axis (leave blank to omit)"},
    {"kind": "entry",       "key": "ylabel",         "label": "Y-axis Label",
     "hint": "Label for the vertical (count) axis (e.g. Count)"},
    {"kind": "double", "label": "X-axis Range", "hint": "Clamp the displayed data range (leave blank for auto)",
     "widget": "entry",
     "fields": [{"key": "vmin", "sublabel": "Min"}, {"key": "vmax", "sublabel": "Max"}]},

    {"kind": "section", "label": "Figure Size"},
    {"kind": "double", "label": "Figure Size (per panel)", "hint": "Width and height in inches for each histogram panel",
     "widget": "entry",
     "fields": [{"key": "figsize_w", "sublabel": "W"}, {"key": "figsize_h", "sublabel": "H"}]},

    {"kind": "section", "label": "Font"},
    {"kind": "entry", "key": "font",        "label": "Font",        "hint": "Font family (e.g. DejaVu Sans)"},
    {"kind": "entry", "key": "font_size",   "label": "Font Size",   "hint": "Font size in points"},
    {"kind": "entry", "key": "font_weight", "label": "Font Weight", "hint": "e.g. normal, bold"},
]

# ---------------------------------------------------------------------------
# Type coercion map
# ---------------------------------------------------------------------------

_COERCE_MAP: dict[str, str] = {
    "bins":       "int",
    "font_size":  "float",
    "figsize_w":  "float",
    "figsize_h":  "float",
    "vmin":       "float_or_none",
    "vmax":       "float_or_none",
}

# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------

class HistogramController:
    """Manages the Histogram Settings dialog."""

    def __init__(self, model: Any, view: Any) -> None:
        self.model = model
        self.view = view
        self._dialog: PropertiesView | None = None

    def open(self) -> None:
        """Open the histogram settings dialog, pre-populated from the model."""
        values = self.model.histogram_settings.to_dict()
        self._dialog = PropertiesView(self.view.root, HIST_SCHEMA, values)
        self._dialog.pref_window.title("Histogram Settings")
        self._dialog.save_button.config(command=self._save_and_close)

    def _save_and_close(self) -> None:
        """Write validated values back to HistogramSettings and close the dialog."""
        if self._dialog is None:
            return
        raw_settings = self._dialog.get_settings()
        coerced, invalid = coerce_with_validation(raw_settings, _COERCE_MAP)
        if invalid:
            messagebox.showerror(
                "Invalid Histogram Settings",
                format_invalid_values_message(HIST_SCHEMA, invalid),
                parent=self._dialog.pref_window,
            )
            return
        self.model.histogram_settings.update_from_dict(coerced)
        self._dialog.pref_window.destroy()
        self._dialog = None
