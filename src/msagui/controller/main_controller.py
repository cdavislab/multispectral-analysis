
import logging
import os
from typing import Any, Callable
from msagui.controller.buttons_controller import ButtonsController
from msagui.controller.dropdown_controller import DropDownController
from msagui.controller.listbox_controller import FileListController
from msagui.controller.image_controller import ImageController
from msagui.controller.image_properties_controller import ImagePropertiesController
from msagui.controller.steps_controller import StepsController
from msagui.controller.histogram_controller import HistogramController

logger = logging.getLogger(__name__)

# Controller class to manage the logic between the Model and the View
class ControllerDispatcher:
    def __init__(self, model: Any, view: Any) -> None:
        # Initialize controller with model and view, set up configs and signals
        self.model = model
        self.view = view
        self.steps: Any = None
        self.config: list[str] = ['save_correction_freq1', 'save_correction_freq2', 'save_threshold_freq2','freq1_label',
                      'freq2_label', 'freq1c_label', 'freq2c_label', 'ratio_label']
        self.img_config: list[str] = ['font', 'font_size', 'font_weight', 'cmap', 'vmin', 'vmax', 'cunits', 'ratio_vmin',
                           'ratio_vmax', 'ratio_cunits', 'pixel_scale', 'scale_bar_units', 'scale_bar_color','scale_bar_location',
                        'scale_bar_fixed_value','num_ticks']
        self.recruit_controllers()
        self.connect_signals()
        self.dropdown_ctrl.import_default_settings()
        self.view_length = "Full" #Full, Parent, File
    
    def recruit_controllers(self) -> None:
        """Create and return instances of other controllers"""
        self.listbox_ctrl = FileListController(
            self.model,
            self.view.listbox,
            self.view.view_mode,
            show_groups=self.view.show_groups,
            sort_key=self.view.sort_key,
            sort_desc=self.view.sort_desc,
        )
        self.button_ctrl = ButtonsController(self.model, self.view, self.listbox_ctrl)
        self.dropdown_ctrl = DropDownController(self.model, self.view)
        self.image_properties_ctrl = ImagePropertiesController(self.model, self.view)
        self.image_ctrl = ImageController(self.model, self.view)
        self.steps_ctrl = StepsController(self.model, self.view)
        self.histogram_ctrl = HistogramController(self.model, self.view)
        
    def connect_signals(self) -> None:
        """Attach all dispatcher-managed signals and trace callbacks."""
        self.connect_button_signals()
        self.connect_menu_signals()
        self.connect_accelerators()
        self.connect_listbox_signals()
        self.view.view_mode.trace_add('write', lambda *_: self.listbox_ctrl.update_listbox())
        self.view.show_histograms.trace_add('write', self._on_histogram_toggle)
        self.view.show_groups.trace_add('write', self._on_group_toggle)
        self.view.show_inputs.trace_add('write', self._on_visibility_toggle)
        self.view.show_outputs.trace_add('write', self._on_visibility_toggle)
        self.view.sort_key.trace_add('write', self._on_sort_change)
        self.view.sort_desc.trace_add('write', self._on_sort_change)

    def connect_button_signals(self) -> None:
        """Bind view buttons to controller commands."""
        button_commands = {
            self.view.buttons.items['Add']: self.up(self.button_ctrl.add),
            self.view.buttons.items['Delete']: self.up(self.button_ctrl.delete),
            self.view.buttons.items['Analyze']: self.up(self.button_ctrl.analyze),
            self.view.buttons.items['Export']: self.up(self.button_ctrl.export_images),
            self.view.buttons.items['Set-Up']: self.steps_ctrl.open
            # self.view.buttons.items['Groups']: self.button_ctrl.
        }
        for button, command in button_commands.items():
            button.config(command=command)

    def connect_menu_signals(self) -> None:
        """Bind menu entries to controller actions."""
        self.view.root.bind('<<MenuToggle>>', self.handle_menu_toggle)
        self.view.file_menu.entryconfig('Load Session...', command=self.up(self.dropdown_ctrl.load_session))
        self.view.file_menu.entryconfig('Save Session As...', command=self.dropdown_ctrl.save_session_as)
        self.view.config_menu.entryconfig('General', command=self.up(self.image_properties_ctrl.preferences))
        self.view.export_menu.entryconfig('File List',  command=self.up(self.dropdown_ctrl.export_filelist))
        self.view.export_menu.entryconfig('Settings',   command=self.up(self.dropdown_ctrl.export_settings))
        self.view.export_menu.entryconfig('Default Settings', command=self.up(self.dropdown_ctrl.export_default_settings))
        self.view.export_menu.entryconfig('Logs', command=self.dropdown_ctrl.export_logs)
        self.view.import_menu.entryconfig('File List',  command=self.up(self.dropdown_ctrl.import_filelist))
        self.view.import_menu.entryconfig('Settings',   command=self.up(self.dropdown_ctrl.import_settings))
        self.view.config_menu.entryconfig('Image',     command=self.up(self.image_properties_ctrl.image_preferences))
        self.view.config_menu.entryconfig('Histogram', command=self.histogram_ctrl.open)

    def connect_accelerators(self) -> None:
        """Register keyboard accelerators for common actions."""
        self.view.view_menu.entryconfig('Histograms', accelerator='Ctrl+H')
        sequences = (
            '<Control-h>',
            '<Control-H>',
            '<Control-KeyPress-h>',
            '<Control-KeyPress-H>',
            '<Control-BackSpace>',
        )
        for sequence in sequences:
            self.view.root.bind_all(sequence, self._handle_histogram_shortcut, add=True)

    def _handle_histogram_shortcut(self, event: Any) -> None:
        """Toggle histogram visibility via keyboard shortcut."""
        _ = event
        self.dropdown_ctrl.toggle_checkbox(self.view.show_histograms)
        # trace_add on show_histograms will trigger _on_histogram_toggle automatically
        return 'break'

    def _on_histogram_toggle(self, *_: Any) -> None:
        """Called whenever show_histograms changes; refreshes the current display."""
        self._apply_visibility_filters()
        idx = self.listbox_ctrl.get_listbox_index()
        if idx is None:
            return
        self.image_ctrl.update_display(idx)

    def _on_group_toggle(self, *_: Any) -> None:
        """Called whenever show_groups changes; rebuilds the listbox and refreshes display."""
        self._apply_visibility_filters()
        self.listbox_ctrl.update_listbox()
        idx = self.listbox_ctrl.get_listbox_index()
        if idx is None:
            return
        self.image_ctrl.update_display(idx)

    def _on_visibility_toggle(self, *_: Any) -> None:
        """Called whenever show_inputs/show_outputs changes; rebuild list and refresh display."""
        self._apply_visibility_filters()
        self.listbox_ctrl.update_listbox()
        idx = self.listbox_ctrl.get_listbox_index()
        if idx is None:
            return
        self.image_ctrl.update_display(idx)

    def _on_sort_change(self, *_: Any) -> None:
        """Resort listbox items and refresh current display."""
        self.listbox_ctrl.sort_items()
        self.listbox_ctrl.update_listbox()
        idx = self.listbox_ctrl.get_listbox_index()
        if idx is None:
            return
        self.image_ctrl.update_display(idx)

    def _apply_visibility_filters(self) -> None:
        """Apply input/output visibility flags to metadata items."""
        show_inputs = self.view.show_inputs.get()
        show_outputs = self.view.show_outputs.get()
        for item in self.model.metadata.items:
            if item.kind == "input":
                item.visible = show_inputs
            elif item.kind == "processed":
                item.visible = show_outputs
            else:
                item.visible = True

    def handle_menu_toggle(self, event: Any) -> None:
        """Read current menu state when the menu toggle event fires."""
        _ = event
        _state = {
            'Group View': self.view.view_menu.entrycget('Group View', 'variable'),
            'Histograms': self.view.view_menu.entrycget('Histograms', 'variable'),
            'Show Inputs': self.view.show_inputs.get(),
            'Show Outputs': self.view.show_outputs.get(),
            'View Mode': self.view.view_mode.get()

        }

    def connect_listbox_signals(self) -> None:
        """Bind listbox selection and drag interactions."""
        self.view.listbox.file_list.bind('<<ListboxSelect>>', self._on_file_selection)
        self.view.listbox.file_list.bind('<Button-1>', self.listbox_ctrl.on_click)
        self.view.listbox.file_list.bind('<Up>', self.listbox_ctrl.on_arrow_navigation)
        self.view.listbox.file_list.bind('<Down>', self.listbox_ctrl.on_arrow_navigation)
        self.view.listbox.file_list.bind('<B1-Motion>', self.listbox_ctrl.on_drag_motion)
        self.view.listbox.file_list.bind('<ButtonRelease-1>', self._on_drag_release)
        self.view.listbox.file_list.bind('<Double-Button-1>', self.up(self.listbox_ctrl.rename_item))
        self.view.listbox.file_list.bind('<Control-a>', self.listbox_ctrl.select_all)

    def _on_drag_release(self, event: Any) -> None:
        """Handle drag-release reordering and refresh dependent views."""
        moved = self.listbox_ctrl.on_drag_release(event)
        if not moved:
            return
        self._apply_visibility_filters()
        self.listbox_ctrl.update_listbox()
        idx = self.listbox_ctrl.get_listbox_index()
        if idx is None:
            return
        self.image_ctrl.update_display(idx)
        
    def _steps_view_update(self, event: Any) -> None:
        """Open steps configuration view."""
        _ = event
        self.steps_ctrl.open()

    def _on_file_selection(self, event: Any) -> None:
        """Update filename widget and preview when selection changes."""
        value = self.listbox_ctrl.on_file_selection(event)
        idx = self.listbox_ctrl.get_listbox_index()
        if idx is None:
            return

        if self.view.show_groups.get():
            display_name = self.listbox_ctrl._group_display_name(idx)
        else:
            logger.debug("Selected file: %s", value)
            display_name = os.path.basename(value)
        self.view.get_widget('Filename').update('Filename', display_name)
        self.image_ctrl.update_display(idx)

    def up(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator to update view after function call."""
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            self._apply_visibility_filters()
            self.listbox_ctrl.update_listbox()
            idx = self.listbox_ctrl.get_listbox_index()
            if idx is None:
                return result
            logger.debug("Updating display for index: %s", idx)
            self.image_ctrl.update_display(idx)
            return result
        return wrapper