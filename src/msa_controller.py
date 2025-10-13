import tkinter as tk
from tkinter.filedialog import askopenfilenames, askdirectory
from pathlib import Path
import numpy as np
import pandas as pd
import os
# import cProfile
# from multiprocessing import Pool

# Controller class to manage the logic between the Model and the View
class MultispectralController:
    def __init__(self, model, view):
        # Initialize controller with model and view, set up configs and signals
        self.model = model
        self.view = view
        self.config =['save_correction_freq1', 'save_correction_freq2', 'save_threshold_freq2','freq1_label',
                      'freq2_label', 'freq1c_label', 'freq2c_label', 'ratio_label']
        self.img_config = ['font', 'font_size', 'font_weight', 'cmap', 'vmin', 'vmax', 'cunits', 'ratio_vmin',
                           'ratio_vmax', 'ratio_cunits', 'pixel_scale', 'scale_bar_units', 'scale_bar_color','scale_bar_location',
                        'scale_bar_fixed_value','num_ticks']
        self.connect_signals()
        self.import_default_settings()
        self.view_length = "Full" #Full, Parent, File
        

    # Connect signals from the view to controller methods
    def connect_signals(self):
        # Map UI buttons and menu items to controller methods
        button_commands = {
            self.view.Button_Add: self.add_single_files,
            self.view.Button_Delete: self.delete_files,
            self.view.Button_Analyze: self.analyze_files,
            self.view.Button_ExportFolder: self.set_export_folder,
        }

        # Define command mappings for file menu
        file_menu_commands = {
            'Preferences': self.preferences,
            'Image Config': self.image_preferences,
            'Export Statistics': self.export_stats,
            'Export File List': self.export_filelist,
            'Import File List': self.import_filelist,
            'Export Settings': self.export_settings,
            'Import Settings': self.import_settings,
        }

        # Define command mappings for view menu
        view_menu_commands = {
            'Group View': self.update_listbox,
            'Histograms': self.reselect_index,
            'Show Single-Wavenumber': self.update_listbox,
            'Show Ratios': self.update_listbox,
        }

        # Define command mappings for fpath menu
        fpath_menu_commands = {
            'View Full Path': self.update_listbox,
            'View Parent': self.update_listbox,
            'View File Only': self.update_listbox,
        }

        # Apply commands to buttons
        for button, command in button_commands.items():
            button.config(command=command)

        # Apply commands to file menu
        for label, command in file_menu_commands.items():
            self.view.file_menu.entryconfig(label, command=command)

        # Apply commands to view menu
        for label, command in view_menu_commands.items():
            self.view.view_menu.entryconfig(label, command=command)

        # Apply commands to fpath menu
        for label, command in fpath_menu_commands.items():
            self.view.fpath_menu.entryconfig(label, command=command)

        # Accelerator for "Histograms"
        self.view.view_menu.entryconfig('Histograms', accelerator='Ctrl+H')

        # Bind the accelerator key combination to the open_file function
        self.view.root.bind('<Control-h>', lambda event: (self.toggle_checkbox(self.view.show_histograms), self.reselect_index()))

        # Bind Listbox selection event
        self.view.ListBox_1.bind('<<ListboxSelect>>', self.on_file_selection)
        self.view.ListBox_1.bind('<Button-1>', self.on_click)
        self.view.ListBox_1.bind('<Double-Button-1>', self.rename_item)

        self.text_bg = self.view.ListBox_1.cget('bg')  # Get the default background color of the listbox

    def on_click(self, event):
        # Handle listbox selection logic with Ctrl/Shift support
        # Get the current selection index
        index = self.view.ListBox_1.nearest(event.y)
        
        # Check whether Ctrl or Shift is pressed
        ctrl_pressed = (event.state & 0x0004) != 0  # Check for Control key
        shift_pressed = (event.state & 0x0001) != 0  # Check for Shift key

        # Handle selection logic
        if not ctrl_pressed and not shift_pressed:
            # Deselect all other items if no modifier key is pressed
            self.view.ListBox_1.selection_clear(0, tk.END)

        # If Shift is pressed, select a range of items
        if shift_pressed:
            # Get the indices of current selection
            selected_indices = self.view.ListBox_1.curselection()
            if selected_indices:
                # Select the first selected index
                start_index = selected_indices[0]
                # Select items between the last selected index and the current index
                if start_index < index:
                    self.view.ListBox_1.selection_set(start_index, index)
                else:
                    self.view.ListBox_1.selection_set(index, start_index)

        # If Ctrl is pressed, toggle the current item without affecting others
        if ctrl_pressed:
            if self.view.ListBox_1.selection_includes(index):
                self.view.ListBox_1.selection_clear(index)
            else:
                self.view.ListBox_1.selection_set(index)

        # Highlight the selected items
        self.update_selection()

    def update_selection(self):
        # Update listbox item background based on selection
        # Get the indices of selected items
        selected_indices = self.view.ListBox_1.curselection()
        for i in range(self.view.ListBox_1.size()):
            if i in selected_indices:
                self.view.ListBox_1.itemconfig(i, {'bg': 'light blue'})  # Change background color for selected
            else:
                self.view.ListBox_1.itemconfig(i, {'bg': self.text_bg})      # Reset background color for unselected

    def rename_item(self, event):
        # Allow renaming of group items in the listbox
        if not self.view.show_groups.get():  # Check if groups are shown
            return

        selected_index = self.view.ListBox_1.curselection()
        if not selected_index:  # Check if any item is selected
            return
        
        index = selected_index[0]  # Get the first selected index
        current_value = self.view.ListBox_1.get(index)  # Get the current value
        
        # Prompt user for new name using simpledialog
        new_value = tk.simpledialog.askstring("Rename Item", "Enter new name:", initialvalue=current_value)
        if new_value is not None:  # Check if user didn't cancel
            self.model.set_group_name(new_value, index+1)  # Set the new name
        self.update_listbox()

        return

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
        if self.is_number(value):
            self.model.set_pref(key, float(value))
        else:
            print(f"Invalid value for {key}: {value}")

    def is_number(self, s):
        # Utility: check if string can be converted to float
        try:
            float(s)
            return True
        except ValueError:
            return False

    def export_settings(self):
        # Export current settings to a text file
        file_path = tk.filedialog.asksaveasfilename(
        defaultextension=".txt",  # Default file extension
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],  # Supported file types
        title="Save Settings As"
    )
        if file_path == '':  # If the user cancels the save dialog, return
            return

        settings = self.view.get_settings()
        settings.update(self.model.get_preferences())
        # Save dictionary to a text file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(repr(settings))

        return

    def import_default_settings(self):
        # Import default settings from file if available
        if not os.path.exists('msa_options.txt'):
            self.model.set_pref('filetype','.jpg')
            return
        # # Get the absolute path of the currently running Python file
        # current_file_path = os.path.abspath(__file__)

        # # Remove the file name and append 'msa_options.txt'
        # directory_path = os.path.dirname(current_file_path)
        # default = os.path.join(directory_path, 'msa_options.txt')
        self.import_settings('msa_options.txt')
        return

    def import_settings(self, file_path = None):
        # Import settings from a file and update UI/model
        if file_path == None:
            file_path = tk.filedialog.askopenfilename(
            defaultextension=".txt",  # Default file extension
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],  # Supported file types
            title="Save Settings As"
        )
        if file_path == '':  # If the user cancels the save dialog, return
            return
        
        # Read dictionary from the text file
        with open(file_path, 'r', encoding='utf-8') as file:
            settings = eval(file.read())

        entries = {
            'freq1': self.view.entries['freq1'],
            'freq2': self.view.entries['freq2'],
            'freq1c': self.view.entries['freq1c'],
            'freq2c': self.view.entries['freq2c'],
            'freq1cf': self.view.entries['freq1cf'],
            'freq2cf': self.view.entries['freq2cf'],
            'threshold': self.view.entries['threshold']
        }

        for key, entry in entries.items():
            if key in settings:
                entry.delete(0, tk.END)  # Clear the entry
                entry.insert(0, settings.get(key, ''))  # Insert new value

        if 'export_folder' in settings:
            self.view.Button_ExportFolder['text'] = settings.get('export_folder', '')
            self.model.set_pref('export_folder', settings.get('export_folder', ''))

        # Set boolean variables based on the settings dictionary
        # TODO: Put this in model
        self.view.show_groups.set(settings.get('show_groups', False))
        self.view.show_single.set(settings.get('show_single', True))
        self.view.show_ratio.set(settings.get('show_ratio', True))
        self.view.show_histograms.set(settings.get('show_histograms', False))

        self.model.set_pref('filetype', settings.get('export_filetype', '.jpg'))

        # Set view_length if the key exists
        self.view_length = settings.get('view_mode', 'full')

        for key in self.img_config:
            if key in settings:
                self.model.set_pref(key,settings[key])
        
        self.update_listbox()

    def toggle_checkbox(self, checkbox):
        # Toggle a Tkinter BooleanVar checkbox
        if checkbox.get():
            checkbox.set(False)
        else:
            checkbox.set(True)
        return
    
    def add_single_files(self):
        # Open file dialog and add selected files
        progress = self.view.ProgressBar(title="Adding Files")
        files = askopenfilenames(filetypes=(("Comma Delimited", "*.csv"), ("All files", "*.*"),))
        self.add_files(files, progress)
        return
    def add_files(self, files, progress):
        # Add files to the model, handle errors, update progress
        if len(files) == 0:
            progress.destroy()
            return
        outpath = self.model.get_dir(files[0])
        error_files = dict()
        increment = 100 / len(files)
        # processes_pool = Pool(len(files))
        # try:
        #     processes_pool.starmap(self.model.add_files, [(file, outpath) for file in files])
        # except Exception as e:
        #     print(f"Exception caught in main process: {e}")
        # finally:
        #     processes_pool.close()
        #     processes_pool.join()
        ## Error handling for adding files

        for i, file in enumerate(files):
            try:
                self.model.add_files(file, outpath)
            except ValueError as e:
                error_files[file] = e
                continue
            progress.update_progress(increment*i)
        self.update_listbox()

        progress.destroy()
        if len(error_files.keys()) > 0:
            print("Error loading the following files:")
            for key in error_files.keys():
                print(f"{key} : {error_files[key]}")
            self.view.show_error(error_files)
        return
        

    def delete_files(self):
        # Delete selected files from listbox and model
        idx_to_del = list(self.view.ListBox_1.curselection())
        idx_to_del.sort()
        for i in range(len(idx_to_del)):
            self.view.ListBox_1.delete(idx_to_del[i] - i)
        self.model.df = self.model.df.drop(idx_to_del).reset_index(drop=True)
        self.update_listbox()


    #TODO: Troubleshoot addition of dictionaries and swap to freq1 vs lw
    def validate_entries(self):
        # Validate user input fields before analysis
        # Ignore analyze request if no files are loaded
        if self.model.df.empty:
            tk.messagebox.showerror("Add Files", "Add files using \"Add Files\" button before analyzing.")
            return None
        if self.view.show_groups.get():
            tk.messagebox.showerror("Group View", "Cannot analyze in group view.")
            return None
        if not self.view.show_single.get():
            tk.messagebox.showerror("Single Wavenumber", "Please select at least two non-ratio images to analyze.")
            return None
        # Get the values from the entries
        entry_keys = ('freq1', 'freq2', 'freq1c', 'freq2c', 'threshold', 'freq1cf', 'freq2cf')
        args = self.view.get_settings()
        args = {key: args[key] for key in entry_keys}
        # Check if required fields are empty
        if any(args[key] == '' for key in ['freq1', 'freq2']):
            tk.messagebox.showerror("Missing Fields", "Please fill out all fields before analyzing.")
            return None
        # Convert the string inputs to floats
        for key in ['threshold','freq1cf', 'freq2cf']:
            s = args[key]
            try:
                args[key] = float(s) if s.strip() else 0.0
            except ValueError:
                tk.messagebox.showerror("Invalid Input", "Please enter an integer or decimal for the number of wavenumbers.")
                return None
            
        
        # If the correction factor is non-zero, but no correction factor label is entered, show an error
        if ('' == args['freq1c']) and (args['freq1cf'] != 0):
            tk.messagebox.showerror("Missing Fields", "Please enter a label for Frequency 1 Correction.")
            return None
        if ('' == args['freq2c']) and (args['freq2cf'] != 0):
            tk.messagebox.showerror("Missing Fields", "Please enter a label for Frequency 2 Correction.")
            return None
        # If the correction factor for frequency is 0, set correction factor label to None
        if args['freq1cf'] == 0:
            args['freq1c'] = None
        if args['freq2cf'] == 0:
            args['freq2c'] = None
        # If the view has multiple corrections/factors, add them to args
        if hasattr(self.view, 'multiple_corrections') and hasattr(self.view, 'multiple_factors'):
            args['multiple_corrections'] = self.view.multiple_corrections
            args['multiple_factors'] = self.view.multiple_factors
        return args

    def count_unique_types(self, entries):
        # Count unique types among frequency/correction entries
        types = set([entries['freq1'],
                 entries['freq2'],
                 entries['freq1c'],
                 entries['freq2c']])
        if None in types:
            types.remove(None)
        return len(types)

    def profile_analyze_files(self):
        # Profile the analyze_files method (for debugging/performance)
        cProfile.runctx('self.analyze_files()',globals(), locals(), "profile_analyze_files.txt")
        return

    def get_df_indices(self):
        # Get dataframe indices corresponding to selected listbox items
        # Mimic the listbox view with a dataframe slice
        selected_indices = list(self.view.ListBox_1.curselection())
        vsettings = self.view.get_settings()
        desired_groups = []
        if vsettings['show_single']: # Show
            desired_groups += ['Freq1', 'Freq2', 'Freq1c', 'Freq2c', None]
        if vsettings['show_ratio']:
            desired_groups.append('Ratio')
        listbox_df = self.model.df.loc[self.model.df['type'].isin(desired_groups)]
        # Select positional indices in dataframe from the listbox
        selection = listbox_df.iloc[selected_indices,:]
        # Return real dataframe indices
        return selection.index

    def analyze_files(self):
        # Run analysis on selected files/groups, update progress
        # Validate user inputs and prepare them for model method
        entries = self.validate_entries()
        if entries is None:
            return
        progress = self.view.ProgressBar(title="Analyzing Files")
        selected_idx = self.get_df_indices()
        unique_types = self.count_unique_types(entries)
        groups = self.model.pre_analyze_files(entries, selected_idx, unique_types)
        if groups is None:
            progress.destroy()
            tk.messagebox.showinfo("More Files Needed", "Select more files of the same group to analyze")
            return
        increment = 100 / len(groups)
        progress.update_progress(1)
        for group_idx in groups:
            self.model.analyze_files(entries, group_idx)
            progress.update_progress(increment*group_idx)
        self.update_listbox()
        progress.destroy()

    def set_export_folder(self):
        # Set export folder and optionally move files there
        directory = askdirectory()
        self.model.set_pref('export_folder', directory)
        self.view.Button_ExportFolder['text'] = directory
        
        if not self.model.df.empty:
            self.move_files_to_export()
        
        return
    
    def move_files_to_export(self):
        # Move all exported files to the new export folder
        # Prompt user if they want to move the files to the new export folder
        if not tk.messagebox.askyesno("Move Files", "Would you like to move the files to the new export folder?"):
            return
        # If the user selects yes, move the files to the new export folder
        # Take all of the img_path and hist_path files and move them to the new export folder
        for i in range(len(self.model.df)):
            try:
                img_path = self.model.df.loc[i, 'im_path']
                hist_path = self.model.df.loc[i, 'hist_path']
                img_path_new = os.path.join(self.model.get_pref('export_folder'), os.path.basename(img_path))
                hist_path_new = os.path.join(self.model.get_pref('export_folder'), os.path.basename(hist_path))
                os.rename(img_path, img_path_new)
                os.rename(hist_path, hist_path_new)
                self.model.df.loc[i, 'im_path'] = img_path_new
                self.model.df.loc[i, 'hist_path'] = hist_path_new
            except Exception as e:
                tk.messagebox.showerror("Error", f"Error moving file: {e}")
        
        # Check if the model has groups
        if not (hasattr(self.model, 'group_images') and hasattr(self.model, 'group_histograms')):
            return

        # Move the group and histogram files located in the varirables self.model.group_images and self.model.group_histograms
        for i in range(len(self.model.group_images)):
            try:
                group_path = self.model.group_images[i]
                group_path_new = os.path.join(self.model.get_pref('export_folder'), os.path.basename(group_path))
                os.rename(group_path, group_path_new)
                self.model.group_images[i] = group_path_new
            except Exception as e:
                tk.messagebox.showerror("Error", f"Error moving file: {e}")
        #Do the same for self.model.group_histograms
        for i in range(len(self.model.group_histograms)):
            try:
                group_path = self.model.group_histograms[i]
                group_path_new = os.path.join(self.model.get_pref('export_folder'), os.path.basename(group_path))
                os.rename(group_path, group_path_new)
                self.model.group_histograms[i] = group_path_new
            except Exception as e:
                tk.messagebox.showerror("Error", f"Error moving file: {e}")
        return

    def reselect_index(self):
        # Reselect and update display for current index
        # self.view.ListBox_1.select_clear(0, tk.END)  # Clear previous selection
        # self.view.ListBox_1.select_set(self.index)        # Select the specified index
        # self.view.ListBox_1.activate(self.index)          # Make it the active item
        # index = self.view.ListBox_1.curselection()
        # if len(index) == 0:
        #     return
        self.update_display(self.index)
        return
        

    def update_listbox(self):
        # Update the listbox display based on current view settings
        self.model.df = self.model.df.sort_values(by=["group", "fpath"], ascending=[True, True], ignore_index=True)

        self.view.ListBox_1.delete(0, tk.END)
        vsettings = self.view.get_settings()
        if self.view.show_groups.get(): # List only groups in the listbox
            max_group_number = self.model.df['group'].max()
            group_names = self.model.get_group_names()
            for i in range(max_group_number):
                self.view.ListBox_1.insert(tk.END, group_names[i])
            return
        
        desired_groups = []
        if vsettings['show_single']: # Show
            desired_groups += ['Freq1', 'Freq2', 'Freq1c', 'Freq2c', None]
        if vsettings['show_ratio']:
            desired_groups.append('Ratio')
        listbox_df = self.model.df.loc[self.model.df['type'].isin(desired_groups)]

        # Determine if column should read full path or just filename
        if (vsettings['view_mode'] == "full"):
            listbox_series = listbox_df['fpath']
        elif vsettings['view_mode'] == "parent":
            listbox_series = listbox_df['fpath'].apply(lambda x: os.path.basename(os.path.dirname(x)) + "/" + os.path.basename(x))
        elif vsettings['view_mode'] == "file":
            listbox_series = listbox_df['fname']
        else:
            print("Warning:", vsettings['view_mode'],
                  "is not a valid view mode. Defaulting to full path.")
            listbox_series = listbox_df['fpath']
        
        self.view.ListBox_1.insert(tk.END, *listbox_series.values)

        return

    def display_images(self, index):
        # Display images for selected index/group
        """"""
        #What's next: You've just changed the index to the index of the dataframe. Make sure all
        # subsequent code works
        if self.view.show_groups.get():
            group = self.model.df.loc[index,'group'].unique()[0]
            self.view.display(self.model.get_group_image(group))
            return
        
        df_slice = self.model.get_df_slice(index)
        self.view.display(self.model.get_single_image(df_slice))
        return

    def display_histograms(self, index):
        # Display histograms for selected index/group
        if self.view.show_groups.get():
            group = self.model.df.loc[index,'group'].unique()[0]
            self.view.display(self.model.get_group_histogram(group))
            return
        
        df_slice = self.model.get_df_slice(index)
        self.view.display(self.model.get_single_histogram(df_slice))
        return
        

    def display_statistics(self, index):
        # Display statistics for selected index/group
        if self.view.show_groups.get():
            stats = "Statistics"
            self.view.Button_Statistics.configure(text=stats)
            return
        stats = self.model.df[['Mean', 'Median', 'Max_Signal', 'Standard Deviation', 'Standard Error', 'Count']]
        stats = np.round(stats.iloc[index,:].astype(float), 3)
        stats = ("Mean:" + str(stats.iloc[0]) + ", Median:" + str(stats.iloc[1]) +
                 ", Max:" + str(stats.iloc[2]) + ", Stdev:" + str(stats.iloc[3]) +
                 ", SE:" + str(stats.iloc[4]) + ",  Count: " + str(int(stats.iloc[5])))
        self.view.Button_Statistics.configure(text=stats)

    def get_listbox_index(self):
        # Get currently selected listbox index
        return self.view.ListBox_1.curselection()[0]

    def convert_index(self, index: int) -> pd.Index:
        """Convert listbox index to dataframe index by sorting out single wavenumber,
        ratio, or histograms if needbe. Return array of indices if group is selected"""
        if self.view.show_groups.get(): #TODO Check: May need to convert to listbox type to integer
            group = self.get_listbox_index()
            idx = self.model.df['group'] == group + 1
            single_group_df = self.model.df.loc[idx,:]
            df_idx = single_group_df.index
            return df_idx.tolist()

        # Create dataframe that mimics what is shown in the listbox
        viewed_types = []
        if self.view.show_single.get():
            viewed_types += ['Freq1', 'Freq2', 'Freq1c', 'Freq2c', None]
        if self.view.show_ratio.get():
            viewed_types.append('Ratio')
        listbox_df = self.model.df.loc[self.model.df['type'].isin(viewed_types)]
        df_idx = listbox_df.index[index]
        # Return the index of the dataframe that corresponds to the index of the listbox
        return df_idx.tolist()

    def on_file_selection(self, evt):
        # Handle listbox selection event, update display
        w = evt.widget
        if len(w.curselection()) == 0:
            return
        self.index = int(w.curselection()[0])
        value = w.get(self.index)
        self.view.Button_Filename.configure(text=Path(value).stem)
        self.update_display(self.index)
        return
    
    def update_display(self, listbox_idx):
        # Update image/histogram/statistics display for selected index
        df_idx = self.convert_index(listbox_idx)
        if self.view.show_histograms.get():
            self.display_histograms(df_idx)
        else:
            self.display_images(df_idx)
        self.display_statistics(df_idx)
        return

    def export_stats(self):
        # Export statistics using the model
        self.model.export_stats()

    def export_filelist(self):
        # Export current file list to a text file
        file_path = tk.filedialog.asksaveasfilename(
            defaultextension=".txt",  # Default file extension
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],  # Supported file types
            title="Save Settings As"
        )
        if file_path == '':  # If the user cancels the save dialog, return
            return
        
        self.model.export_filelist(file_path)

    # def profile_import_filelist(self):
    #     cProfile.runctx('self.import_filelist()',globals(), locals(), "profile_import_filelist.txt")
    #     return
    def import_filelist(self):
        # Import a list of files from a file and add them
        progress = self.view.ProgressBar(title="Adding Files")
        file_of_files = askopenfilenames(filetypes=(("Comma Delimited", "*.txt"), ("All files", "*.*"),))
        if len(file_of_files) == 0:
            progress.destroy()
            return
        file_df = pd.read_csv(file_of_files[0])
        file_df = file_df[~file_df.applymap(lambda x: isinstance(x, str) and "ratio" in x.lower()).any(axis=1)]
        filelist = file_df['fpath'].tolist()
        self.add_files(filelist, progress)
        return