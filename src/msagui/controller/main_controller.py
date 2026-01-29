
from msagui.controller.buttons_controller import ButtonsController
from msagui.controller.dropdown_controller import DropDownController
from msagui.controller.file_list_controller import FileListController
from msagui.controller.image_controller import ImageController
from msagui.controller.image_properties_controller import ImagePropertiesController
from msagui.controller.steps_controller import StepsController
# Controller class to manage the logic between the Model and the View
class ControllerDispatcher:
    def __init__(self, model, view):
        # Initialize controller with model and view, set up configs and signals
        self.model = model
        self.view = view
        self.config =['save_correction_freq1', 'save_correction_freq2', 'save_threshold_freq2','freq1_label',
                      'freq2_label', 'freq1c_label', 'freq2c_label', 'ratio_label']
        self.img_config = ['font', 'font_size', 'font_weight', 'cmap', 'vmin', 'vmax', 'cunits', 'ratio_vmin',
                           'ratio_vmax', 'ratio_cunits', 'pixel_scale', 'scale_bar_units', 'scale_bar_color','scale_bar_location',
                        'scale_bar_fixed_value','num_ticks']
        self.recruit_controllers()
        self.connect_signals()
        # self.import_default_settings()
        self.view_length = "Full" #Full, Parent, File
    
    def recruit_controllers(self):
        """Create and return instances of other controllers"""
        self.button = ButtonsController(self.model, self.view)
        self.dropdown = DropDownController(self.model, self.view)
        self.file_list = FileListController(self.model, self.view)
        self.image_properties = ImagePropertiesController(self.model, self.view)
        self.image = ImageController(self.model, self.view)
        self.steps = StepsController(self.model, self.view)
        
    def connect_signals(self):
        self.connect_button_signals()
        self.connect_menu_signals()
        self.connect_accelerators()
        self.connect_listbox_signals()

    def connect_button_signals(self):
        button_commands = {
            self.view.buttons['Add']: self.up(self.button.add),
            self.view.buttons['Delete']: self.up(self.button.delete),
            self.view.buttons['Analyze']: self.up(self.button.analyze),
            self.view.buttons['Export Folder']: self.up(self.button.set_export_folder),
        }
        for button, command in button_commands.items():
            button.config(command=command)

    def connect_menu_signals(self):
        self.view.root.bind('<<MenuToggle>>', self.handle_menu_toggle)
        file_menu_commands = {
            'Preferences': self.up(self.image_properties.preferences),
            'Image Config': self.up(self.image_properties.image_preferences),
            'Export Statistics': self.up(self.dropdown.export_stats),
            'Export File List': self.up(self.dropdown.export_filelist),
            'Import File List': self.up(self.dropdown.import_filelist),
            'Export Settings': self.up(self.dropdown.export_settings),
            'Import Settings': self.up(self.dropdown.import_settings),
        }
        # view_menu_commands = {
        #     'Group View': self.dropdown.update_listbox,
        #     'Histograms': self.dropdown.reselect_index,
        #     'Show Single-Wavenumber': self.dropdown.update_listbox,
        #     'Show Ratios': self.dropdown.update_listbox,
        # }
        # fpath_menu_commands = {
        #     'View Full Path': self.dropdown.update_listbox,
        #     'View Parent': self.dropdown.update_listbox,
        #     'View File Only': self.dropdown.update_listbox,
        # }
        for label, command in file_menu_commands.items():
            self.view.file_menu.entryconfig(label, command=command)
        # for label, command in view_menu_commands.items():
        #     self.view.view_menu.entryconfig(label, command=command)
        # for label, command in fpath_menu_commands.items():
        #     self.view.fpath_menu.entryconfig(label, command=command)

    def connect_accelerators(self):
        self.view.view_menu.entryconfig('Histograms', accelerator='Ctrl+H')
        self.view.root.bind('<Control-h>', self._handle_histogram_shortcut)

    def _handle_histogram_shortcut(self, event):
        self.dropdown.toggle_checkbox(self.view.show_histograms)
        # self.file_list.reselect_index()

    def handle_menu_toggle(self, event):
        state = {
            'Group View': self.view.view_menu.entrycget('Group View', 'variable'),
            'Histograms': self.view.view_menu.entrycget('Histograms', 'variable'),
            'Show Single-Wavenumber': self.view.view_menu.entrycget('Show Single-Wavenumber', 'variable'),
            'Show Ratios': self.view.view_menu.entrycget('Show Ratios', 'variable'),
            'View Mode': self.view.view_mode.get()

        }

    def connect_listbox_signals(self):
        self.view.file_list.bind('<<ListboxSelect>>', self.up(self.file_list.on_file_selection))
        # self.view.file_list.bind('<Button-1>', self.up(self.file_list.on_click))
        self.view.file_list.bind('<Double-Button-1>', self.up(self.file_list.rename_item))
        
    def up(self, func):
        """Decorator to update view after function call."""
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            self.file_list.update_listbox()
            idx = self.file_list.get_listbox_index()
            # if len(idx) == 0:
            #     return result
            print("Updating display for index:", idx)
            self.image.update_display(idx)
            return result
        return wrapper