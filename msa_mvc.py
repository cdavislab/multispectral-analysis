import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import warnings
from pathlib import Path
import multispectral_analysis as msa

# Model class to handle data operations and business logic
class MultispectralModel:
    def __init__(self):
        # Initialize an empty DataFrame with specific columns
        self.df = pd.DataFrame(columns=['fpath', 'fname', 'im_path', 'hist_path', 'group',
                                        'Mean', 'Median', 'Max_Signal', 'Standard Deviation',
                                        'Standard Error', 'Count'])
        self.files = []  # List to hold file paths
        self.isAnalyzed = False  # Flag to check if files are analyzed
        self.dpi = 300  # DPI setting for image saving
        self.export_folder = "msa_analysis"  # Default export folder
        self.show_fullpath = False  # Flag to show full file paths
        self.subdivide_files = True  # Flag to subdivide files into folders

    # Function to match a target file in a list of CSVs by removing a specific wavenumber from file names
    def match_csv(self, csv1, csv_wavenum, target):
        for line in csv1:
            if line.replace(csv_wavenum, "") == target:
                return line
        warnings.warn("Warning: " + target + " could not be matched to natural/correction files")
        return

    # Function to group files based on wavenumbers
    def group_files(self, file_list, label_wavenum, natural_wavenum,
                    label_correction_wavenum, natural_correction_wavenum):
        label_csvs = []
        natural_csvs = []
        correction_csvs = []
        excess_csvs = []
        correction_wavenum = label_correction_wavenum
        correction_wavenum = natural_correction_wavenum
        # TODO: Have two separate correction wavenumbers
        # Categorize files into label, natural, correction, and excess groups
        for line in file_list:
            if label_wavenum in line:
                label_csvs.append(line)
            elif natural_wavenum in line:
                natural_csvs.append(line)
            elif correction_wavenum in line:
                correction_csvs.append(line)
            else:
                excess_csvs.append(line)

        groups = []
        # Create groups of related files (label, natural, correction)
        for i in range(len(label_csvs)):
            target = label_csvs[i].replace(label_wavenum, "")
            groups.append([label_csvs[i]])
            groups[i].append(self.match_csv(natural_csvs, natural_wavenum, target))
            groups[i].append(self.match_csv(correction_csvs, correction_wavenum, target))

        # Iterate through the groups and assign group numbers
        for group_number, group in enumerate(groups):
            self.df.loc[self.df['fpath'].isin(group), 'group'] = group_number

        print(self.df[['fname','group']])
        return

    # Function to save an image representation of a wavenumber data file
    def save_wavenum_image(self, filepath, title):
        self.save_image(np.loadtxt(filepath, delimiter=','), title)
        return

    # Function to save a data array as an image
    def save_image(self, data, title):
        plt.clf()
        plt.imshow(data, cmap='CMRmap', vmin=0)
        plt.colorbar()
        plt.savefig(title + ".jpg", dpi=self.dpi)
        return

    # Function to compute ratio images from label, natural, and correction files
    def ratio_images(self, label_data, natural_data, label_correction_data, natural_correction_data, lcf, ncf, threshold):
        # Correct data and compute ratios
        label_corrected = msa.correct_spectra(label_data, label_correction_data, lcf)
        natural_corrected = msa.correct_spectra(natural_data, natural_correction_data, ncf)
        natural_thresholded, _ = msa.threshold(natural_corrected, threshold)
        ratio = msa.compute_ratio(label_corrected, natural_thresholded)
        return ratio

    # Function to sort files in a group into label, natural, and correction
    def sort_wavenumbers(self, group, label_wavenum, natural_wavenum, 
                         label_correction_wavenum, natural_correction_wavenum):
        for file in group:
            if label_wavenum in file:
                label_file = file
            elif natural_wavenum in file:
                natural_file = file
            elif label_correction_wavenum in file:
                label_correction_file = file
            elif natural_correction_wavenum in file:
                natural_correction_file = file
            else:
                warnings.warn("Warning: " + file + " could not be sorted into a wavenumber group")
        if label_correction_wavenum == natural_correction_wavenum:
            natural_correction_file = label_correction_file
        return label_file, natural_file, label_correction_file, natural_correction_file

    # Function to add files to the model and process them
    def add_files(self, files):
        outfolder = self.export_folder
        if self.subdivide_files:
            parent = Path(files[0]).parent.name
            outfolder = os.path.join(self.export_folder, parent)
        Path(outfolder).mkdir(parents=True, exist_ok=True)

        # Add each unique file to the DataFrame with a summary and create an image
        for file in files:
            if file not in self.df['fpath'].unique():
                outpath = os.path.join(outfolder, Path(file).stem)
                image_path = outpath + ".jpg"
                summary = msa.summarize(np.loadtxt(file, delimiter=','))
                summary = list(summary[0].astype('float'))
                self.df.loc[self.df.shape[0]] = [file, Path(file).stem, image_path, "", 0] + summary
                self.save_wavenum_image(file, outpath)

    # Function to analyze files and compute ratio images
    def analyze_files(self, label_wavenum, natural_wavenum, label_correction_wavenum, natural_correction_wavenum, threshold, lcf, natural_cf):
        
        correction_wavenum = natural_correction_wavenum
        
        
        self.group_files(self.df['fpath'], label_wavenum, natural_wavenum,
                        label_correction_wavenum, natural_correction_wavenum)
        
        groups = self.df['group'].unique()
        for group_idx in groups:
            group = self.df[self.df['group'] == group_idx]['fpath'].values
            label_file, natural_file, label_correction_file, natural_correction_file = self.sort_wavenumbers(group, label_wavenum, natural_wavenum,
                                                                              label_correction_wavenum, natural_correction_wavenum)
            label_data = np.loadtxt(label_file, delimiter=',')
            natural_data = np.loadtxt(natural_file, delimiter=',')
            label_correction_data = np.loadtxt(label_correction_file, delimiter=',') #Don't load twice if not necessary #TODO
            natural_correction_data = np.loadtxt(natural_correction_file, delimiter=',')

            ratio = self.ratio_images(label_data, natural_data, label_correction_data, natural_correction_data,
                                      lcf, natural_cf, threshold)
            ratio_fname = Path(label_file).stem.replace(label_wavenum, "") + "_ratio"
            ratio_im_path = os.path.join(self.export_folder, ratio_fname)
            self.save_image(ratio, ratio_im_path)
            summary = msa.summarize(ratio)
            summary = list(summary[0].astype('float'))
            self.df.loc[self.df.shape[0]] = [ratio_fname, ratio_fname, ratio_im_path + ".jpg", "", group_idx] + summary
    # Function to export the statistics to a CSV file
    def export_stats(self):
        self.df.to_csv(os.path.join(self.export_folder, "Summary.csv"), mode='a')

import tkinter as tk
import tkinter.font as tkFont
from tkinter.filedialog import askopenfilenames, askdirectory
from pathlib import Path
from PIL import ImageTk, Image

# View class to handle the GUI components
class MultispectralView:
    def __init__(self, root):
        self.root = root
        self.setup_ui()

    # Function to setup the GUI layout and components
    def setup_ui(self):
        self.root.title("Multispectral Analysis")
        width = 800
        height = 500
        screenwidth = self.root.winfo_screenwidth()
        screenheight = self.root.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        self.root.geometry(alignstr)
        self.root.resizable(True, True)

        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(3, weight=1)
        self.root.columnconfigure(3, weight=1)
        self.root.rowconfigure(5, weight=1)
        self.root.columnconfigure(5, weight=1)

        frm = tk.Frame(self.root)
        frm.grid(row=0, column=0, rowspan=7, columnspan=2, sticky="nsew", padx=2, pady=2)
        scrollbar = tk.Scrollbar(frm, orient="horizontal")
        scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.ListBox_1 = tk.Listbox(frm, xscrollcommand=scrollbar.set, borderwidth="1px", fg="#333333",
                                    justify="center", font=('Times', 10))
        self.ListBox_1.pack(expand=True, fill=tk.BOTH)
        scrollbar.config(command=self.ListBox_1.xview)

        self.Button_Add = tk.Button(self.root, bg="#e9e9ed", fg="#000000", justify="center",
                                    font=('Times', 10), text="Add Files")
        self.Button_Add.grid(row=7, column=0, rowspan=1, columnspan=2, sticky="nsew", padx=2)

        self.Button_Delete = tk.Button(self.root, bg="#e9e9ed", fg="#000000", justify="center",
                                       font=('Times', 10), text="Delete Files")
        self.Button_Delete.grid(row=8, column=0, rowspan=1, columnspan=2, sticky="nsew", padx=2)

        self.Button_Analyze = tk.Button(self.root, bg="#e9e9ed", fg="#000000", justify="center",
                                        font=('Times', 10), text="Analyze")
        self.Button_Analyze.grid(row=9, column=0, rowspan=2, columnspan=2, sticky="nsew", padx=2)

        self.img_panel = tk.Label(self.root)
        self.panel_img = ""
        self.img_panel.grid(row=0, column=2, rowspan=9, columnspan=4, sticky="nsew", padx=2, pady=2)

        self.Button_Filename = tk.Button(self.root, bg="#e9e9ed", fg="#000000",
                                         justify="center", font=('Times', 10),
                                         text="Filename")
        self.Button_Filename.grid(row=9, column=2, rowspan=1, columnspan=4, sticky="nsew", padx=2)

        self.Button_Statistics = tk.Button(self.root, bg="#e9e9ed", fg="#000000",
                                           justify="center", font=('Times', 10),
                                           text="Statistics")
        self.Button_Statistics.grid(row=10, column=2, rowspan=1, columnspan=4, sticky="nsew", padx=2)

        nw_text = tk.Label(self.root, bg="#e9e9ed", fg="#333333",
                           justify="left", font=('Times', 10),
                           text="Natural (cm-1):")
        nw_text.grid(row=11, column=0, rowspan=1, columnspan=1, sticky="nsew")
        
        nw = tk.StringVar()
        self.nw_entry = tk.Entry(self.root, textvariable=nw, font=('Times', 10, 'normal'))
        self.nw_entry.grid(row=11, column=1, rowspan=1, columnspan=1, sticky="nsew")

        ncw_text = tk.Label(self.root, bg="#e9e9ed", fg="#333333", justify="left",
                            font=tkFont.Font(family='Times', size=10),
                            text="Natural Correction (cm-1):")
        ncw_text.grid(row=11, column=2, rowspan=1, columnspan=1, sticky="nsew")

        ncw = tk.StringVar()
        self.ncw_entry = tk.Entry(self.root, textvariable=ncw, font=('Times', 10, 'normal'))
        self.ncw_entry.grid(row=11, column=3, rowspan=1, columnspan=1, sticky="nsew")

        ncf_text = tk.Label(self.root, bg="#e9e9ed", fg="#333333", justify="left",
                            font=tkFont.Font(family='Times', size=10),
                            text="Natural Correction Factor:")
        ncf_text.grid(row=11, column=4, rowspan=1, columnspan=1, sticky="nsew")

        natural_cf = tk.StringVar()
        self.ncf_entry = tk.Entry(self.root, textvariable=natural_cf,
                                  font=('Times', 10, 'normal'))
        self.ncf_entry.grid(row=11, column=5, rowspan=1, columnspan=1, sticky="nsew")

        lw_text = tk.Label(self.root, bg="#e9e9ed", fg="#333333", justify="left",
                           font=tkFont.Font(family='Times', size=10),
                           text="Label (cm-1):")
        lw_text.grid(row=12, column=0, rowspan=1, columnspan=1, sticky="nsew")

        label_wavenum = tk.StringVar()
        self.lw_entry = tk.Entry(self.root, textvariable=label_wavenum,
                                 font=('Times', 10, 'normal'))
        self.lw_entry.grid(row=12, column=1, rowspan=1, columnspan=1, sticky="nsew")

        lcw_text = tk.Label(self.root, bg="#e9e9ed", fg="#333333", justify="left",
                            font=tkFont.Font(family='Times', size=10),
                            text="Label Correction (cm-1):")
        lcw_text.grid(row=12, column=2, rowspan=1, columnspan=1, sticky="nsew")

        lcw = tk.StringVar()
        self.lcw_entry = tk.Entry(self.root, textvariable=lcw,
                                  font=('Times', 10, 'normal'))
        self.lcw_entry.grid(row=12, column=3, rowspan=1, columnspan=1, sticky="nsew")

        lcf_text = tk.Label(self.root, bg="#e9e9ed", fg="#333333", justify="left",
                            font=tkFont.Font(family='Times', size=10),
                            text="Label Correction Factor:")
        lcf_text.grid(row=12, column=4, rowspan=1, columnspan=1, sticky="nsew")

        lcf = tk.StringVar()
        self.lcf_entry = tk.Entry(self.root, textvariable=lcf,
                                  font=('Times', 10, 'normal'))
        self.lcf_entry.grid(row=12, column=5, rowspan=1, columnspan=1, sticky="nsew")

        threshold_text = tk.Label(self.root, bg="#e9e9ed", fg="#333333", justify="left",
                                  font=tkFont.Font(family='Times', size=10),
                                  text="Threshold")
        threshold_text.grid(row=13, column=4, rowspan=1, columnspan=1, sticky="nsew")

        threshold = tk.StringVar()
        self.threshold_entry = tk.Entry(self.root, textvariable=threshold,
                                        font=('Times', 10, 'normal'))
        self.threshold_entry.grid(row=13, column=5, rowspan=1, columnspan=1, sticky="nsew")

        self.nw_entry.insert(0, "1744")
        self.lw_entry.insert(0, "1703")
        self.ncw_entry.insert(0, "1655")
        self.lcw_entry.insert(0, "1655")
        self.ncf_entry.insert(0, ".31")
        self.lcf_entry.insert(0, ".61")
        self.threshold_entry.insert(0, "0.15")

        Button_ExportFolder = tk.Button(self.root, bg="#e9e9ed", fg="#333333", justify="center",
                                        font=tkFont.Font(family='Times', size=10),
                                        text="Export Folder:")
        Button_ExportFolder.grid(row=13, column=0, rowspan=1, columnspan=1, sticky="nsew")
        self.Button_ExportFolder = Button_ExportFolder

        self.Listbox_ExportFolder = tk.Label(self.root, bg="#e9e9ed", fg="#333333",
                                             justify="left", font=('Times', 10),
                                             text="Export Folder Path")
        self.Listbox_ExportFolder.grid(row=13, column=1, rowspan=1, columnspan=3, sticky="nsew")

        self.menubar = tk.Menu(self.root)
        self.settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.settings_menu.add_command(label="Open Config")
        self.settings_menu.add_command(label="Save Config")
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.file_menu.add_command(label="Export Statistics")
        self.root.config(menu=self.menubar)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        self.menubar.add_cascade(label="Settings", menu=self.settings_menu)

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
        self.view.ListBox_1.bind('<<ListboxSelect>>', self.on_file_selection)

    # Method to handle adding files
    def add_files(self):
        files = askopenfilenames(filetypes=(("Comma Delimited", "*.csv"), ("All files", "*.*"),))
        self.model.add_files(files)
        self.update_listbox()

    # Method to handle deleting files
    def delete_files(self):
        idx_to_del = list(self.view.ListBox_1.curselection())
        idx_to_del.sort()
        for i in range(len(idx_to_del)):
            self.view.ListBox_1.delete(idx_to_del[i] - i)
        self.model.df = self.model.df.drop(idx_to_del).reset_index(drop=True)
        self.update_listbox()

    # Method to handle analyzing files
    def analyze_files(self):
        self.model.analyze_files(self.view.lw_entry.get(),
                                 self.view.nw_entry.get(),
                                 self.view.lcw_entry.get(),
                                 self.view.ncw_entry.get(),
                                 float(self.view.threshold_entry.get()),
                                 float(self.view.lcf_entry.get()),
                                 float(self.view.ncf_entry.get()))
        print("I'm about to update listbox in analyze files")
        self.update_listbox()

    # Method to handle setting the export folder
    def set_export_folder(self):
        self.model.export_folder = askdirectory()
        self.view.Listbox_ExportFolder['text'] = self.model.export_folder

    # Method to update the listbox in the view
    def update_listbox(self):
        self.model.df = self.model.df.sort_values(by=["group", "fpath"], ascending=[True, True], ignore_index=True)

        self.view.ListBox_1.delete(0, tk.END)
        if self.model.show_fullpath:
            self.view.ListBox_1.insert(tk.END, *self.model.df['fpath'].values)
            return
        self.view.ListBox_1.insert(tk.END, *self.model.df['fname'].values)
        return

    # Method to display selected image in the view
    def display_images(self, index):
        im_path = self.model.df['im_path'][index]
        img_width = self.view.img_panel.winfo_width()
        img_height = self.view.img_panel.winfo_height()

        self.view.panel_img = ImageTk.PhotoImage(Image.open(im_path).resize((img_width, img_height)))
        self.view.img_panel.configure(image=self.view.panel_img)
        return

    # Method to display statistics of the selected file in the view
    def display_statistics(self, index):
        stats = self.model.df[['Mean', 'Median', 'Max_Signal', 'Standard Deviation', 'Standard Error', 'Count']]
        stats = np.round(stats.iloc[index,:].astype(float), 3)
        stats = ("Mean:" + str(stats[0]) + ", Median:" + str(stats[1]) +
                 ", Max:" + str(stats[2]) + ", Stdev:" + str(stats[3]) +
                 ", SE:" + str(stats[4]) + ",  Count: " + str(int(stats[5])))
        self.view.Button_Statistics.configure(text=stats)

    # Method to handle file selection from the listbox
    def on_file_selection(self, evt):
        w = evt.widget
        index = int(w.curselection()[0])
        value = w.get(index)
        self.view.Button_Filename.configure(text=Path(value).stem)
        self.display_images(index)
        self.display_statistics(index)

    def export_stats(self):
        self.model.export_stats()

if __name__ == "__main__":
    root = tk.Tk()
    model = MultispectralModel()
    view = MultispectralView(root)
    controller = MultispectralController(model, view)
    root.mainloop()
