import tkinter as tk
from tkinter import ttk
class PropertiesView:
    """Dialog for editing main preferences."""
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
        # Build the form fields for preferences
        if len(args) != 9:
            raise ValueError("Expected exactly 9 arguments. Got {}".format(len(args)))

        (export_filetype,
        save_correction_freq1_val,
        save_correction_freq2_val,
        export_threshold_val,
        freq1_label, freq2_label,
        freq1c_label, freq2c_label,
        ratio_label) = args

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
        self.make_label("Labels")
        self.make_form("Frequency 1 Label", 
                        "Label for frequency 1 in group images",
                        "entry", freq1_label)
        self.make_form("Frequency 2 Label", 
                        "Label for frequency 2 in group images",
                        "entry", freq2_label)
        self.make_form("Frequency 1 Correction Label", 
                        "Label for frequency 1 correction in group images",
                        "entry", freq1c_label)
        self.make_form("Frequency 2 Correction Label", 
                        "Label for frequency 2 correction in group images",
                        "entry", freq2c_label)
        self.make_form("Ratio Label", 
                        "Label for ratio in group images",
                        "entry", ratio_label)
        return

    def make_label(self, label):
        # Make a bold section label
        #Make a bold label
        label = tk.Label(self.pref_frame, text=label, font=("Verdana", 10, "bold"))
        label.grid(row=self.row, column=0, columnspan=1, sticky='w', padx=self.padx_label)
        self.row += 1
        return

    def make_separator(self):
        # Add a separator line
        separator = ttk.Separator(self.pref_frame, orient='horizontal')
        separator.grid(row=self.row, column=0, columnspan=5, sticky='ew')
        self.row += 1
        return
    def make_form(self, title, hint, type_of_entry, variable):
        # Generalized form field creation
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
        # Generalized double form field creation
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
        # Get value from a form field
        return self.properties[title]["entry"].get()
    
    def get_setting_keys(self):
        # Get all setting keys
        return self.properties.keys()
    
class ImagePropertiesView(PropertiesView):
    """Dialog for editing image preferences."""
    def __init__(self, root, *args):
        super().__init__(root, *args)
        self.pref_window.title("Image Preferences")
        self.pref_frame.pack()
        return

    def _create_widgets(self, *args):
        # Build the form fields for image preferences
        [font, font_size, font_weight, cmap, vmin, vmax, cunits,
            ratio_vmin, ratio_vmax, ratio_cunits, pixel_scale,
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
        self.make_double_form("Scale", "Minimum and max of ratio color bar", "entry", ("rMin", ratio_vmin), ("rMax", ratio_vmax))
        self.make_form("Ratio Units", "Units of the ratio color bar", "entry", ratio_cunits)
        self.make_label("Scale")
        self.make_form("Pixel Scale", "Change the scale of the pixels", "entry", pixel_scale)
        self.make_form("Scale Bar Units", "Units of the scale bar", "entry", scale_bar_units)
        self.make_form("Scale Bar Color", "(e.g. white or black)", "entry", scale_bar_color)
        self.make_form("Scale Bar Location", "(e.g. upper/lower left)", "entry", scale_bar_location)
        self.make_form("Scale Bar Fixed Value", "(e.g. '10' for 10 units)", "entry", scale_bar_fixed_value)

        self.make_label("Extra")
        self.make_form("Number of Tick Marks", "Number of axis tick markers", "entry", num_ticks)
        return