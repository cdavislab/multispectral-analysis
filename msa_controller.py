import tkinter as tk
from tkinter.filedialog import askopenfilenames, askdirectory
from pathlib import Path
from PIL import ImageTk, Image
import numpy as np
import pandas as pd
import os

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
        self.view.Button_Add.config(command=self.add_files)
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
        self.view.view_menu.entryconfig('Full File Path', command=self.change_label_and_update)

        # Bind the accelerator key combination to the open_file function
        self.view.root.bind('<Control-h>', lambda event: (self.toggle_checkbox(self.view.show_histograms),self.reselect_index()))

    def preferences(self):
        self.properties = self.view.PropertiesView(
            self.view.root,self.model.get_ext())
        self.properties.save_button.config(command=self.pref_save_and_quit)
        return

    def pref_save_and_quit(self):
        self.model.set_ext(self.properties.export_filetype_entry.get())
        self.properties.pref_window.destroy()
        return

    def export_settings(self):
        file_path = tk.filedialog.asksaveasfilename(
        defaultextension=".txt",  # Default file extension
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],  # Supported file types
        title="Save Settings As"
    )

        settings = {'lw': self.view.lw_entry.get(),
                    'nw': self.view.nw_entry.get(),
                    'lcw': self.view.lcw_entry.get(),
                    'ncw': self.view.ncw_entry.get(),
                    'threshold': self.view.threshold_entry.get(),
                    'lcf': self.view.lcf_entry.get(),
                    'ncf': self.view.ncf_entry.get(),
                    'export_folder': self.model.export_folder,
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
        # Get the absolute path of the currently running Python file
        current_file_path = os.path.abspath(__file__)

        # Remove the file name and append 'msa_options.txt'
        directory_path = os.path.dirname(current_file_path)
        default = os.path.join(directory_path, 'msa_options.txt')
        self.import_settings(default)
        return

    def import_settings(self, file_path = None):
        if file_path == None:
            file_path = tk.filedialog.askopenfilename(
            defaultextension=".txt",  # Default file extension
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],  # Supported file types
            title="Save Settings As"
        )
        
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
            self.model.export_folder = settings.get('export_folder', '')

        # Set boolean variables based on the settings dictionary
        self.view.show_groups.set(settings.get('show_groups', False))
        self.view.show_single.set(settings.get('show_single', True))
        self.view.show_ratio.set(settings.get('show_ratio', True))
        self.view.show_histograms.set(settings.get('show_histograms', False))
        self.view.show_histograms.set(settings.get('show_histograms', False))

        self.model.set_ext(settings.get('export_filetype', '.jpg'))
        # Set view_length if the key exists
        self.view_length = settings.get('view_length', 'Full')

        self.update_listbox()

    def change_label_and_update(self):
        current_label = self.view.view_menu.entrycget(4, 'label')
        if current_label == "Full File Path":
            self.view.view_menu.entryconfig(4, label="Parent Folder")
            self.view_length = "Parent"
        elif current_label == "Parent Folder":
            self.view.view_menu.entryconfig(4, label="Filename")
            self.view_length = "File"
        elif current_label == "Filename":
            self.view.view_menu.entryconfig(4, label="Full File Path")
            self.view_length = "Full"
        else:
            raise ValueError("Invalid label")
        self.update_listbox()
        return

    def toggle_checkbox(self, checkbox):
        if checkbox.get():
            checkbox.set(False)
        else:
            checkbox.set(True)
        return
    
    def add_files(self):
        files = askopenfilenames(filetypes=(("Comma Delimited", "*.csv"), ("All files", "*.*"),))
        if len(files) == 0:
            return
        errors = self.model.add_files(files)
        self.update_listbox()
        # If there are errors, show them in a dialog box
        if errors:
            self.view.show_error(errors)
        return
        

    def delete_files(self):
        idx_to_del = list(self.view.ListBox_1.curselection())
        idx_to_del.sort()
        for i in range(len(idx_to_del)):
            self.view.ListBox_1.delete(idx_to_del[i] - i)
        self.model.df = self.model.df.drop(idx_to_del).reset_index(drop=True)
        self.update_listbox()

    def analyze_files(self):
        self.model.analyze_files(self.view.lw_entry.get(),
                                 self.view.nw_entry.get(),
                                 self.view.lcw_entry.get(),
                                 self.view.ncw_entry.get(),
                                 float(self.view.threshold_entry.get()),
                                 float(self.view.lcf_entry.get()),
                                 float(self.view.ncf_entry.get()))
        self.update_listbox()

    def set_export_folder(self):
        self.model.export_folder = askdirectory()
        self.view.Button_ExportFolder['text'] = self.model.export_folder
        
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
                img_path_new = os.path.join(self.model.export_folder, os.path.basename(img_path))
                hist_path_new = os.path.join(self.model.export_folder, os.path.basename(hist_path))
                os.rename(img_path, img_path_new)
                os.rename(hist_path, hist_path_new)
                self.model.df.loc[i, 'img_path'] = img_path_new
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
                group_path_new = os.path.join(self.model.export_folder, os.path.basename(group_path))
                os.rename(group_path, group_path_new)
                self.model.group_images[i] = group_path_new
            except Exception as e:
                tk.messagebox.showerror("Error", f"Error moving file: {e}")
        #Do the same for self.model.group_histograms
        for i in range(len(self.model.group_histograms)):
            try:
                group_path = self.model.group_histograms[i]
                group_path_new = os.path.join(self.model.export_folder, os.path.basename(group_path))
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

        if self.view.show_groups.get(): # List only groups in the listbox
            max_group_number = self.model.df['group'].max()
            for i in range(max_group_number + 1):
                self.view.ListBox_1.insert(tk.END, f"Image {i}")
            return
        
        desired_groups = []
        if self.view.show_single.get(): # Show
            desired_groups += ['Natural', 'Label', 'Natural_Corr', 'Label_Corr', None]
        if self.view.show_ratio.get():
            desired_groups.append('Ratio')
        listbox_df = self.model.df.loc[self.model.df['type'].isin(desired_groups)]

        # Determine if column should read full path or just filename
        if self.view_length == "Full":
            listbox_series = listbox_df['fpath']
        elif self.view_length == "Parent":
            listbox_series = listbox_df['fpath'].apply(lambda x: os.path.basename(os.path.dirname(x)) + "/" + os.path.basename(x))
        else:
            listbox_series = listbox_df['fname']
        
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
        stats = self.model.df[['Mean', 'Median', 'Max_Signal', 'Standard Deviation', 'Standard Error', 'Count']]
        stats = np.round(stats.iloc[index,:].astype(float), 3)
        stats = ("Mean:" + str(stats[0]) + ", Median:" + str(stats[1]) +
                 ", Max:" + str(stats[2]) + ", Stdev:" + str(stats[3]) +
                 ", SE:" + str(stats[4]) + ",  Count: " + str(int(stats[5])))
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

    def import_filelist(self):
        file_of_files = askopenfilenames(filetypes=(("Comma Delimited", "*.csv"), ("All files", "*.*"),))
        df = pd.read_csv(file_of_files[0])
        self.model.import_filelist(df)
        self.update_listbox()