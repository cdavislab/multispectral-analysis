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

    # Connect signals from the view to controller methods
    def connect_signals(self):
        self.view.Button_Add.config(command=self.add_files)
        self.view.Button_Delete.config(command=self.delete_files)
        self.view.Button_Analyze.config(command=self.analyze_files)
        self.view.Button_ExportFolder.config(command=self.set_export_folder)
        # self.view.menubar.entryconfig("Export Statistics", command=self.export_stats)
        # self.view.root.config(menu=self.view.menubar)
        self.view.file_menu.entryconfig('Export Statistics', command=self.export_stats)
        self.view.file_menu.entryconfig('Export File List', command=self.export_filelist)
        self.view.file_menu.entryconfig('Import File List', command=self.import_filelist)
        self.view.ListBox_1.bind('<<ListboxSelect>>', self.on_file_selection)

        self.view.view_menu.entryconfig('View Groups', command=self.update_listbox)
        self.view.view_menu.entryconfig('Show Single-Wavenumber', command=self.update_listbox)
        self.view.view_menu.entryconfig('Show Ratios', command=self.update_listbox)

    def add_files(self):
        files = askopenfilenames(filetypes=(("Comma Delimited", "*.csv"), ("All files", "*.*"),))
        self.model.add_files(files)
        self.update_listbox()

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

    def update_listbox(self):
        self.model.df = self.model.df.sort_values(by=["group", "fpath"], ascending=[True, True], ignore_index=True)

        self.view.ListBox_1.delete(0, tk.END)

        # Determine if column should read full path or just filename
        if self.model.show_fullpath:
            col = 'fpath'
        elif self.model.show_parent:
            raise NotImplementedError #TODO: Implement parent folder showing too
        else:
            col = 'fname'
        

        if self.view.show_groups.get(): # List only groups in the listbox
            self.view.ListBox_1.insert(tk.END, *self.model.df['group'].unique())
            return
        
        else:
            desired_groups = []
            if self.view.show_single.get(): # Show
                desired_groups += ['Natural', 'Label', 'Natural_Corr', 'Label_Corr', None]
            if self.view.show_ratio.get():
                desired_groups.append('Ratio')
            self.view.ListBox_1.insert(tk.END, *self.model.df.loc[
                (self.model.df['type'].isin(desired_groups)),col]
                .values)

        return

    def display_images(self, index):
        if self.view.show_groups.get():
            self.view.display(self.model.get_group_image(index))
            return
        
        df_slice = self.model.get_df_slice(
            index, self.view.show_groups.get(),
            self.view.show_single.get(), self.view.show_ratio.get())
        self.view.display(self.model.get_single_image(df_slice))
        return

    def display_histograms(self, index):
        if self.view.show_groups.get():
            self.view.display(self.model.get_group_histogram(index))
            return
        
        df_slice = self.model.get_df_slice(
            index, self.view.show_groups.get(),
            self.view.show_single.get(), self.view.show_ratio.get())
        self.view.display(self.model.get_single_histogram(df_slice))
        return
        

    def display_statistics(self, index):
        stats = self.model.df[['Mean', 'Median', 'Max_Signal', 'Standard Deviation', 'Standard Error', 'Count']]
        stats = np.round(stats.iloc[index,:].astype(float), 3)
        stats = ("Mean:" + str(stats[0]) + ", Median:" + str(stats[1]) +
                 ", Max:" + str(stats[2]) + ", Stdev:" + str(stats[3]) +
                 ", SE:" + str(stats[4]) + ",  Count: " + str(int(stats[5])))
        self.view.Button_Statistics.configure(text=stats)

    def on_file_selection(self, evt):
        w = evt.widget
        if len(w.curselection()) == 0:
            return
        index = int(w.curselection()[0])
        value = w.get(index)
        self.view.Button_Filename.configure(text=Path(value).stem)
        self.display_images(index)
        self.display_statistics(index)

    def export_stats(self):
        self.model.export_stats()

    def export_filelist(self):
        self.model.export_filelist()

    def import_filelist(self):
        file_of_files = askopenfilenames(filetypes=(("Comma Delimited", "*.csv"), ("All files", "*.*"),))
        df = pd.read_csv(file_of_files[0])
        self.model.import_filelist(df)
        self.update_listbox()