
import logging
import os
from msagui.controller.buttons_controller import ButtonsController
from msagui.controller.dropdown_controller import DropDownController
from msagui.controller.listbox_controller import FileListController
from msagui.controller.image_controller import ImageController
from msagui.controller.image_properties_controller import ImagePropertiesController
from msagui.controller.steps_controller import StepsController

logger = logging.getLogger(__name__)

# Controller class to manage the logic between the Model and the View
class ControllerDispatcher:
    def __init__(self, model, view):
        # Initialize controller with model and view, set up configs and signals
        self.model = model
        self.view = view
        self.steps = None
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
        self.button_ctrl = ButtonsController(self.model, self.view)
        self.dropdown_ctrl = DropDownController(self.model, self.view)
        self.listbox_ctrl = FileListController(self.model, self.view.listbox)
        self.image_properties_ctrl = ImagePropertiesController(self.model, self.view)
        self.image_ctrl = ImageController(self.model, self.view)
        self.steps_ctrl = StepsController(self.model, self.view)
        
    def connect_signals(self):
        self.connect_button_signals()
        self.connect_menu_signals()
        self.connect_accelerators()
        self.connect_listbox_signals()

    def connect_button_signals(self):
        button_commands = {
            self.view.buttons.items['Add']: self.up(self.button_ctrl.add),
            self.view.buttons.items['Delete']: self.up(self.button_ctrl.delete),
            self.view.buttons.items['Analyze']: self.up(self.button_ctrl.analyze),
            self.view.buttons.items['Export']: self.up(self.button_ctrl.export_images),
            self.view.buttons.items['Frequency']: self.steps_ctrl.open
            # self.view.buttons.items['Groups']: self.button_ctrl.
        }
        for button, command in button_commands.items():
            button.config(command=command)

    def connect_menu_signals(self):
        self.view.root.bind('<<MenuToggle>>', self.handle_menu_toggle)
        file_menu_commands = {
            'Preferences': self.up(self.image_properties_ctrl.preferences),
            'Image Config': self.up(self.image_properties_ctrl.image_preferences),
            'Export Statistics': self.up(self.dropdown_ctrl.export_stats),
            'Export File List': self.up(self.dropdown_ctrl.export_filelist),
            'Import File List': self.up(self.dropdown_ctrl.import_filelist),
            'Export Settings': self.up(self.dropdown_ctrl.export_settings),
            'Import Settings': self.up(self.dropdown_ctrl.import_settings),
        }
        for label, command in file_menu_commands.items():
            self.view.file_menu.entryconfig(label, command=command)

    def connect_accelerators(self):
        self.view.view_menu.entryconfig('Histograms', accelerator='Ctrl+H')
        self.view.root.bind('<Control-h>', self._handle_histogram_shortcut)

    def _handle_histogram_shortcut(self, event):
        self.dropdown_ctrl.toggle_checkbox(self.view.show_histograms)
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
        self.view.listbox.file_list.bind('<<ListboxSelect>>', self.up(self._on_file_selection))
        self.view.listbox.file_list.bind('<Button-1>', self.listbox_ctrl.on_click)
        self.view.listbox.file_list.bind('<Double-Button-1>', self.up(self.listbox_ctrl.rename_item))
        
    def _steps_view_update(self, event):
        self.steps_ctrl.open()

    def _on_file_selection(self, event):
        value = self.listbox_ctrl.on_file_selection(event)
        logging.info(f"Selected file: {value}")
        value = os.path.basename(value)
        self.view.get_widget('Filename').update('Filename', value)

    def up(self, func):
        """Decorator to update view after function call."""
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            self.listbox_ctrl.update_listbox()
            idx = self.listbox_ctrl.get_listbox_index()
            if idx is None:
                return result
            print(f"Updating display for index: {idx}")
            self.image_ctrl.update_display(idx)
            return result
        return wrapper