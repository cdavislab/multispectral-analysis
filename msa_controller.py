import tkinter as tk
from tkinter.filedialog import askopenfilenames, askdirectory
from pathlib import Path
from PIL import ImageTk, Image
import numpy as np
import pandas as pd
import os
import cProfile
from multiprocessing import Pool

# Controller class to manage the logic between the Model and the View
class MultispectralController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.connect_signals()
        self.import_default_settings()
        self.view_length = "Full" #Full, Parent, File
        

    # Connect signals from the view to controller methods
    def connect_signals(self):
        self.view.Button_Add.config(command=self.add_single_files)
        self.view.Button_Delete.config(command=self.delete_files)
        self.view.Button_Analyze.config(command=self.analyze_files)
        self.view.Button_ExportFolder.config(command=self.set_export_folder)
        
        # self.view.menubar.entryconfig("Export Statistics", command=self.export_stats)
        # self.view.root.config(menu=self.view.menubar)
        self.view.file_menu.entryconfig('Preferences', command=self.preferences)
        self.view.file_menu.entryconfig('Export Statistics', command=self.export_stats)
        self.view.file_menu.entryconfig('Export File List', command=self.export_filelist)
        self.view.file_menu.entryconfig('Import File List', command=self.import_filelist)
        self.view.file_menu.entryconfig('Export Settings', command=self.export_settings)
        self.view.file_menu.entryconfig('Import Settings', command=self.import_settings)
        self.view.ListBox_1.bind('<<ListboxSelect>>', self.on_file_selection)

        self.view.view_menu.entryconfig('Group View', command=self.update_listbox)
        self.view.view_menu.entryconfig('Histograms', command=self.reselect_index, accelerator='Ctrl+H')
        self.view.view_menu.entryconfig('Show Single-Wavenumber', command=self.update_listbox)
        self.view.view_menu.entryconfig('Show Ratios', command=self.update_listbox)

        self.view.fpath_menu.entryconfig('View Full Path', command=self.update_listbox)
        self.view.fpath_menu.entryconfig('View Parent', command=self.update_listbox)
        self.view.fpath_menu.entryconfig('View File Only', command=self.update_listbox)
        # Bind the accelerator key combination to the open_file function
        self.view.root.bind('<Control-h>', lambda event: (self.toggle_checkbox(self.view.show_histograms),self.reselect_index()))

    def preferences(self):
        self.properties = self.view.PropertiesView(
            self.view.root,self.model.get_ext(),
            self.model.get_pref('save_correction_freq1'),
            self.model.get_pref('save_correction_freq2'),
            self.model.get_pref('save_threshold_freq2'))
        self.properties.save_button.config(command=self.pref_save_and_quit)
        return

    def pref_save_and_quit(self):
        # TODO: Make separate correction frequencies
        label_to_variable = {"Export File Type": "filetype",
                             "Freq 1:": "save_correction_freq1",
                             "Freq 2:": "save_correction_freq2",
                             "Export Threshold": "save_threshold_freq2"}
        keys = self.properties.get_setting_keys()
        for key in keys: # TODO: check valid preferences first
            print(label_to_variable[key], self.properties.get_setting(key))
            self.model.set_pref(label_to_variable[key], self.properties.get_setting(key))

        self.properties.pref_window.destroy()
        return

    def export_settings(self):
        file_path = tk.filedialog.asksaveasfilename(
        defaultextension=".txt",  # Default file extension
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],  # Supported file types
        title="Save Settings As"
    )
        if file_path == '':  # If the user cancels the save dialog, return
            return

        settings = {'lw': self.view.lw_entry.get(),
                    'nw': self.view.nw_entry.get(),
                    'lcw': self.view.lcw_entry.get(),
                    'ncw': self.view.ncw_entry.get(),
                    'threshold': self.view.threshold_entry.get(),
                    'lcf': self.view.lcf_entry.get(),
                    'ncf': self.view.ncf_entry.get(),
                    'export_folder': self.model.get_pref('export_folder'),
                    'show_groups': self.view.show_groups.get(),
                    'show_single': self.view.show_single.get(),
                    'show_ratio': self.view.show_ratio.get(),
                    'show_histograms': self.view.show_histograms.get(),
                    'view_length': self.view_length,
                    'export_filetype': self.model.get_ext()
                    }
        # Save dictionary to a text file
        with open(file_path, 'w') as file:
            file.write(repr(settings))

        return

    def import_default_settings(self):
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
        if file_path == None:
            file_path = tk.filedialog.askopenfilename(
            defaultextension=".txt",  # Default file extension
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],  # Supported file types
            title="Save Settings As"
        )
        if file_path == '':  # If the user cancels the save dialog, return
            return
        
        # Read dictionary from the text file
        with open(file_path, 'r') as file:
            settings = eval(file.read())

        # Set the settings in the view 
        # Insert values into entries if the keys exist in the dictionary
        # Clear and insert values into entries if the keys exist in the dictionary
        if 'lw' in settings:
            self.view.lw_entry.delete(0, tk.END)  # Clear the entry
            self.view.lw_entry.insert(0, settings.get('lw', ''))  # Insert new value

        if 'nw' in settings:
            self.view.nw_entry.delete(0, tk.END)  # Clear the entry
            self.view.nw_entry.insert(0, settings.get('nw', ''))  # Insert new value

        if 'lcw' in settings:
            self.view.lcw_entry.delete(0, tk.END)  # Clear the entry
            self.view.lcw_entry.insert(0, settings.get('lcw', ''))  # Insert new value

        if 'ncw' in settings:
            self.view.ncw_entry.delete(0, tk.END)  # Clear the entry
            self.view.ncw_entry.insert(0, settings.get('ncw', ''))  # Insert new value

        if 'threshold' in settings:
            self.view.threshold_entry.delete(0, tk.END)  # Clear the entry
            self.view.threshold_entry.insert(0, settings.get('threshold', ''))  # Insert new value

        if 'lcf' in settings:
            self.view.lcf_entry.delete(0, tk.END)  # Clear the entry
            self.view.lcf_entry.insert(0, settings.get('lcf', ''))  # Insert new value

        if 'ncf' in settings:
            self.view.ncf_entry.delete(0, tk.END)  # Clear the entry
            self.view.ncf_entry.insert(0, settings.get('ncf', ''))  # Insert new value
        # Update the text and model export folder if the key exists
        if 'export_folder' in settings:
            self.view.Button_ExportFolder['text'] = settings.get('export_folder', '')
            self.model.set_pref('export_folder', settings.get('export_folder', ''))

        # Set boolean variables based on the settings dictionary
        self.view.show_groups.set(settings.get('show_groups', False))
        self.view.show_single.set(settings.get('show_single', True))
        self.view.show_ratio.set(settings.get('show_ratio', True))
        self.view.show_histograms.set(settings.get('show_histograms', False))
        self.view.show_histograms.set(settings.get('show_histograms', False))

        self.model.set_pref('filetype', settings.get('export_filetype', '.jpg'))
        # Set view_length if the key exists
        self.view_length = settings.get('view_mode', 'full')

        self.update_listbox()

    def toggle_checkbox(self, checkbox):
        if checkbox.get():
            checkbox.set(False)
        else:
            checkbox.set(True)
        return
    
    def add_single_files(self):
        progress = self.view.ProgressBar(title="Adding Files")
        files = askopenfilenames(filetypes=(("Comma Delimited", "*.csv"), ("All files", "*.*"),))
        self.add_files(files, progress)
        return
    def add_files(self, files, progress):
        if len(files) == 0:
            progress.destroy()
            return
        outpath = self.model.get_dir(files[0])
        print("This is the outpath")
        print(outpath)
        error_files = dict()
        increment = 100 / len(files)
        import time
        t0 = time.time()
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
        t1 = time.time()
        print(f"Time to add files: {t1-t0}")
        self.update_listbox()

        progress.destroy()
        if len(error_files.keys()) > 0:
            print("Error loading the following files:")
            for key in error_files.keys():
                print(f"{key} : {error_files[key]}")
            self.view.show_error(error_files)
        return
        

    def delete_files(self):
        idx_to_del = list(self.view.ListBox_1.curselection())
        idx_to_del.sort()
        for i in range(len(idx_to_del)):
            self.view.ListBox_1.delete(idx_to_del[i] - i)
        self.model.df = self.model.df.drop(idx_to_del).reset_index(drop=True)
        self.update_listbox()

    def validate_entries(self):
        # Ignore analyze request if no files are loaded
        if self.model.df.empty:
            tk.messagebox("Add Files", "Add files using \"Add Files\" button before analyzing.")
            return None
        # Get the values from the entries
        args = {"freq1": self.view.lw_entry.get(), # 0
                "freq2": self.view.nw_entry.get(), # 1
                "freq1c": self.view.lcw_entry.get(), # 2
                "freq2c": self.view.ncw_entry.get(), # 3
                "threshold": self.view.threshold_entry.get(), # 4
                "freq1cf": self.view.lcf_entry.get(), # 5
                "freq2cf": self.view.ncf_entry.get()} # 6
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
        return args

    def profile_analyze_files(self):
        cProfile.runctx('self.analyze_files()',globals(), locals(), "profile_analyze_files.txt")
        return
    def analyze_files(self):
        # Potential BUG: Freq1 and Freq are swapped 

        # Validate user inputs and prepare them for model method
        entries = self.validate_entries()
        progress = self.view.ProgressBar(title="Analyzing Files")
        groups = self.model.pre_analyze_files(entries)
        increment = 100 / len(groups)
        progress.update_progress(1)
        import time
        t0 = time.time()
        for group_idx in groups:
            self.model.analyze_files(entries, group_idx)
            progress.update_progress(increment*group_idx)
        t1 = time.time()
        print(f"Time to analyze files: {t1-t0}")
        self.update_listbox()
        progress.destroy()

    def set_export_folder(self):
        directory = askdirectory()
        self.model.set_pref('export_folder', directory)
        self.view.Button_ExportFolder['text'] = directory
        
        if not self.model.df.empty:
            self.move_files_to_export()
        
        return
    
    def move_files_to_export(self):
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
        # self.view.ListBox_1.select_clear(0, tk.END)  # Clear previous selection
        # self.view.ListBox_1.select_set(self.index)        # Select the specified index
        # self.view.ListBox_1.activate(self.index)          # Make it the active item
        # index = self.view.ListBox_1.curselection()
        # if len(index) == 0:
        #     return
        self.update_display(self.index)
        return
        

    def update_listbox(self):
        self.model.df = self.model.df.sort_values(by=["group", "fpath"], ascending=[True, True], ignore_index=True)

        self.view.ListBox_1.delete(0, tk.END)
        vsettings = self.view.get_settings()
        if self.view.show_groups.get(): # List only groups in the listbox
            max_group_number = self.model.df['group'].max()
            for i in range(max_group_number + 1):
                self.view.ListBox_1.insert(tk.END, f"Image {i}")
            return
        
        desired_groups = []
        if vsettings['show_single']: # Show
            desired_groups += ['Natural', 'Label', 'Natural_Corr', 'Label_Corr', None]
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
        if self.view.show_groups.get():
            group = self.model.df.loc[index,'group'].unique()[0]
            self.view.display(self.model.get_group_histogram(group))
            return
        
        df_slice = self.model.get_df_slice(index)
        self.view.display(self.model.get_single_histogram(df_slice))
        return
        

    def display_statistics(self, index):
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

    def get_listbox_group_index(self, index):
        return self.view.ListBox_1.get(index)[6:]

    def convert_index(self, index: int) -> pd.Index:
        """Convert listbox index to dataframe index by sorting out single wavenumber,
        ratio, or histograms if needbe. Return array of indices if group is selected"""
        if self.view.show_groups.get(): #TODO Check: May need to convert to listbox type to integer
            idx = self.model.df['group'] == int(self.get_listbox_group_index(index))
            single_group_df = self.model.df.loc[idx,:]
            df_idx = single_group_df.index
            return df_idx.tolist()

        # Create dataframe that mimics what is shown in the listbox
        viewed_types = []
        if self.view.show_single.get():
            viewed_types += ['Natural', 'Label', 'Natural_Corr', 'Label_Corr', None]
        if self.view.show_ratio.get():
            viewed_types.append('Ratio')
        listbox_df = self.model.df.loc[self.model.df['type'].isin(viewed_types)]
        df_idx = listbox_df.index[index]
        # Return the index of the dataframe that corresponds to the index of the listbox
        return df_idx.tolist()

    def on_file_selection(self, evt):
        w = evt.widget
        if len(w.curselection()) == 0:
            return
        self.index = int(w.curselection()[0])
        value = w.get(self.index)
        self.view.Button_Filename.configure(text=Path(value).stem)
        self.update_display(self.index)
        return
    
    def update_display(self, listbox_idx):
        df_idx = self.convert_index(listbox_idx)
        if self.view.show_histograms.get():
            self.display_histograms(df_idx)
        else:
            self.display_images(df_idx)
        self.display_statistics(df_idx)
        return

    def export_stats(self):
        self.model.export_stats()

    def export_filelist(self):
        self.model.export_filelist()

    def profile_import_filelist(self):
        cProfile.runctx('self.import_filelist()',globals(), locals(), "profile_import_filelist.txt")
        return
    def import_filelist(self):
        # Add no files if the user cancels the dialog #TODO
        progress = self.view.ProgressBar(title="Adding Files")
        file_of_files = askopenfilenames(filetypes=(("Comma Delimited", "*.csv"), ("All files", "*.*"),))
        file_df = pd.read_csv(file_of_files[0])
        file_df = file_df[~file_df.applymap(lambda x: isinstance(x, str) and "ratio" in x.lower()).any(axis=1)]
        filelist = file_df['fpath'].tolist()
        self.add_files(filelist, progress)
        return