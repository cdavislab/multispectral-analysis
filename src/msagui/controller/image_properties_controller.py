from msagui.model.msa_utils import is_number

class ImagePropertiesController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
    def preferences(self):
        # Open preferences dialog for main settings
        prefs = [self.model.get_pref(key) for key in self.config]
        
        self.properties = self.view.PropertiesView(
            self.view.root,
            self.model.get_ext(),
            *prefs)
        self.properties.save_button.config(command=self.pref_save_and_quit)
        return

    def pref_save_and_quit(self):
        # Save preferences from dialog and close it
        # TODO: Make separate correction frequencies
        label_to_variable = {"Export File Type": "filetype",
                                "Freq 1:": "save_correction_freq1",
                                "Freq 2:": "save_correction_freq2",
                                "Export Threshold": "save_threshold_freq2",
                                "Frequency 1 Label": "freq1_label",
                                "Frequency 2 Label": "freq2_label",
                                "Frequency 1 Correction Label": "freq1c_label",
                                "Frequency 2 Correction Label": "freq2c_label",
                                "Ratio Label": "ratio_label",}
        keys = self.properties.get_setting_keys()
        for key in keys: # TODO: check valid preferences first
            self.model.set_pref(label_to_variable[key], self.properties.get_setting(key))

        self.properties.pref_window.destroy()
        return

    def image_preferences(self):
        # Open preferences dialog for image settings
        preferences = self.model.get_preferences()
        image_preferences = [preferences[key] for key in self.img_config]
        
        if preferences['vmin'] == None:
            idx = self.img_config.index('vmin')
            image_preferences[idx] = ''
        if preferences['vmax'] == None:
            idx = self.img_config.index('vmax')
            image_preferences[idx] = ''
        if preferences['ratio_vmin'] == None:
            idx = self.img_config.index('ratio_vmin')
            image_preferences[idx] = ''
        if preferences['ratio_vmax'] == None:
            idx = self.img_config.index('ratio_vmax')
            image_preferences[idx] = ''
        self.image_properties = self.view.ImagePropertiesView(
            self.view.root, *image_preferences)

        self.image_properties.save_button.config(command=self.image_pref_save_and_quit)
        return

    def image_pref_save_and_quit(self):
        # Save image preferences from dialog and close it
        label_to_variable = {"Font": "font", #string
                                "Font Size": "font_size", #float
                                "Font Weight": "font_weight", #string
                                "Color Map": "cmap", #string
                                "Units": "cunits", #string 
                                "Min": "vmin",
                                "Max": "vmax",
                                "rMin": "ratio_vmin",
                                "rMax": "ratio_vmax",
                                "Ratio Units": "ratio_cunits", #string
                                "Pixel Scale": "pixel_scale", #float
                                "Scale Bar Units": "scale_bar_units", #string
                                "Scale Bar Color": "scale_bar_color", #string
                                "Scale Bar Location": "scale_bar_location", #string
                                "Scale Bar Fixed Value": "scale_bar_fixed_value", #float
                                "Number of Tick Marks": "num_ticks"} # float
        
        keys = self.image_properties.get_setting_keys()
        for key in keys: # TODO: check valid preferences first
            self.model.set_pref(label_to_variable[key], self.image_properties.get_setting(key))

        for key in {"Min": "vmin", "Max": "vmax", "Scale Bar Fixed Value": "scale_bar_fixed_value",
                    "rMin": "ratio_vmin", "rMax": "ratio_vmax"}:
            value = self.image_properties.get_setting(key)
            if value == '':
                value = None
            else:
                value = float(value)
            self.model.set_pref(label_to_variable[key], value)



        self.image_properties.pref_window.destroy()
        pass

    def save_string_pref(self, key, value):
        # Save a string preference to the model
        self.model.set_pref(key, value)
        return
    
    def save_float_pref(self, key, value):
        # Save a float preference to the model, with validation
        if is_number(value):
            self.model.set_pref(key, float(value))
        else:
            print(f"Invalid value for {key}: {value}")