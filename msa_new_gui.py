import tkinter as tk
import tkinter.font as tkFont
from tkinter.filedialog import askdirectory
import sys
import numpy as np
from numpy import genfromtxt
import pandas as pd
import matplotlib.pyplot as plt
import csv
import os
import multispectral_analysis as msa
import warnings
from pathlib import Path
from PIL import ImageTk,Image
#TODO: Add a menu
#TODO: Add pop-out menu for easier file selection
#TODO: Save images to folder and grab files from folder to display
#TODO: Display images
#TODO: Display images when selected from listbox
#TODO: Add labels to file selection
#TODO: Make statistics appear when selected from listbox
#TODO: Implement save button for statistics

class App:

####################################
#############  GUI  ################
####################################

    def __init__(self, root):
        

        self.df = pd.DataFrame(columns=['fpath','fname','im_path','hist_path',
                                        'Mean', 'Median','Standard Deviation',
                                        'Standard Error', 'Size', 'Max_Signal'])
        self.files = []
        self.isAnalyzed = False
        self.dpi = 300
        self.export_folder = "msa_analysis"
        self.show_fullpath = False
        self.subdivide_files = True

        #setting title
        root.title("Multispectral Analysis")
        
        #setting window size
        width=800
        height=500
        screenwidth = root.winfo_screenwidth()
        screenheight = root.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2,
                                    (screenheight - height) / 2)
        root.geometry(alignstr)
        root.resizable(True, True) 

        ####################################
        ######## LEFT PANEL WIDGETS ########
        ####################################

        root.rowconfigure(1, weight=1)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(3, weight=1)
        root.columnconfigure(3, weight=1)
        root.rowconfigure(5, weight=1)
        root.columnconfigure(5, weight=1)

        # File name listbox, scrollbar, and frame that encapsulates them
        frm = tk.Frame(root)
        frm.grid(row=0, column=0, rowspan=7, columnspan=2, sticky="nsew",padx=2,pady=2)
        scrollbar = tk.Scrollbar(frm, orient="horizontal")
        scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.ListBox_1=tk.Listbox(frm, xscrollcommand=scrollbar.set, borderwidth="1px", fg="#333333",
                                  justify="center", font=('Times',10))
        self.ListBox_1.pack(expand=True, fill=tk.BOTH)
        self.ListBox_1.bind('<<ListboxSelect>>', self.On_File_Selection)
        scrollbar.config(command=self.ListBox_1.xview)

        # Add, Delete, and Analyze Buttons
        Button_Add=tk.Button(root,bg="#e9e9ed",fg="#000000",justify="center",
                             font=('Times',10),text="Add Files",
                             command=self.Button_Add_command)
        Button_Add.grid(row=7, column=0, rowspan=1, columnspan=2, sticky="nsew",padx=2)

        Button_Delete=tk.Button(root,bg="#e9e9ed",fg="#000000",justify="center",
                                font=('Times',10), text="Delete Files",
                                command=self.Button_Delete_command)
        Button_Delete.grid(row=8, column=0, rowspan=1, columnspan=2, sticky="nsew",padx=2)

        Button_Analyze=tk.Button(root,bg="#e9e9ed",fg="#000000",justify="center",
                                font=('Times',10), text="Analyze",
                                command=self.Button_Analyze_command)
        Button_Analyze.grid(row=9, column=0, rowspan=2, columnspan=2, sticky="nsew",padx=2)

        # ####################################
        # ######## RIGHT PANEL WIDGETS #######
        # ####################################

        self.img_panel = tk.Label(root)
        self.panel_img = ""
        self.img_panel.grid(row=0, column=2, rowspan=9, columnspan=4, sticky="nsew",padx=2, pady=2)

        self.Button_Filename=tk.Button(root,bg="#e9e9ed",fg="#000000",
                                       justify="center", font=('Times',10),
                                       text="Filename")
        self.Button_Filename.grid(row=9, column=2, rowspan=1, columnspan=4, sticky="nsew",padx=2)

        self.Button_Statistics=tk.Button(root,bg="#e9e9ed",fg="#000000",
                                         justify="center", font=('Times',10),
                                         text="Statistics")
        self.Button_Statistics.grid(row=10, column=2, rowspan=1, columnspan=4, sticky="nsew",padx=2)

        # ####################################
        # ########## ENTRY WIDGETS ###########
        # ####################################

        # Natural Wavenumber (nw)
        nw_text=tk.Label(root,bg="#e9e9ed",fg="#333333",
                         justify="left", font=('Times',10),
                         text="Natural (cm-1):")
        nw_text.grid(row=11, column=0, rowspan=1, columnspan=1, sticky="nsew")
        
        # Natural Wavenumber (nw) Entry
        nw=tk.StringVar()
        self.nw_entry = tk.Entry(root,textvariable = nw, font=('Times',10,'normal'))
        self.nw_entry.grid(row=11, column=1, rowspan=1, columnspan=1, sticky="nsew")

        # Natural Correction Wavenumber (ncw)
        ncw_text=tk.Label(root,bg="#e9e9ed",fg="#333333",justify="left",
                          font=tkFont.Font(family='Times',size=10),
                          text="Natural Correction (cm-1):")
        ncw_text.grid(row=11, column=2, rowspan=1, columnspan=1, sticky="nsew")

        # Natural Correction Wavenumber (ncw) Entry
        ncw=tk.StringVar()
        self.ncw_entry = tk.Entry(root,textvariable = ncw,font=('Times',10,'normal'))
        self.ncw_entry.grid(row=11, column=3, rowspan=1, columnspan=1, sticky="nsew")

        # Natural Correction Factor (ncf)
        ncf_text=tk.Label(root,bg="#e9e9ed",fg="#333333",justify="left",
                          font=tkFont.Font(family='Times',size=10),
                          text="Natural Correction Factor:")
        ncf_text.grid(row=11, column=4, rowspan=1, columnspan=1, sticky="nsew")

        natural_cf=tk.StringVar()
        self.ncf_entry = tk.Entry(root,textvariable = natural_cf,
                                    font=('Times',10,'normal'))
        self.ncf_entry.grid(row=11, column=5, rowspan=1, columnspan=1, sticky="nsew")

        # Label Wavenumber (lw)
        lw_text=tk.Label(root,bg="#e9e9ed",fg="#333333",justify="left",
                          font=tkFont.Font(family='Times',size=10),
                          text="Label (cm-1):")
        lw_text.grid(row=12, column=0, rowspan=1, columnspan=1, sticky="nsew")

        label_wavenum=tk.StringVar()
        self.lw_entry = tk.Entry(root,textvariable = label_wavenum,
                                       font=('Times',10,'normal'))
        self.lw_entry.grid(row=12, column=1, rowspan=1, columnspan=1, sticky="nsew")

        # Label Correction Wavenumber (lcw)
        lcw_text=tk.Label(root,bg="#e9e9ed",fg="#333333",justify="left",
                          font=tkFont.Font(family='Times',size=10),
                          text="Label Correction (cm-1):")
        lcw_text.grid(row=12, column=2, rowspan=1, columnspan=1, sticky="nsew")

        lcw=tk.StringVar()
        self.lcw_entry = tk.Entry(root,textvariable = lcw,
                             font=('Times',10,'normal'))
        self.lcw_entry.grid(row=12, column=3, rowspan=1, columnspan=1, sticky="nsew")

        # Label Correction Factor (lcf)
        lcf_text=tk.Label(root,bg="#e9e9ed",fg="#333333",justify="left",
                          font=tkFont.Font(family='Times',size=10),
                          text="Label Correction Factor:")
        lcf_text.grid(row=12, column=4, rowspan=1, columnspan=1, sticky="nsew")
        
        lcf=tk.StringVar()
        self.lcf_entry = tk.Entry(root,textvariable = lcf,
                             font=('Times',10,'normal'))
        self.lcf_entry.grid(row=12, column=5, rowspan=1, columnspan=1, sticky="nsew")
        
        # Threshold
        threshold_text=tk.Label(root,bg="#e9e9ed",fg="#333333",justify="left",
                          font=tkFont.Font(family='Times',size=10),
                          text="Threshold")
        threshold_text.grid(row=13, column=4, rowspan=1, columnspan=1, sticky="nsew")
        
        threshold=tk.StringVar()
        self.threshold_entry = tk.Entry(root,textvariable = threshold,
                             font=('Times',10,'normal'))
        self.threshold_entry.grid(row=13, column=5, rowspan=1, columnspan=1, sticky="nsew")

        self.nw_entry.insert(0, "1744")
        self.lw_entry.insert(0, "1703")
        self.ncw_entry.insert(0, "1655")
        self.lcw_entry.insert(0, "1655")
        self.ncf_entry.insert(0, ".31")
        self.lcf_entry.insert(0, ".61")
        self.threshold_entry.insert(0,"0.15")

        # Open Analysis Folder Button
        Button_ExportFolder=tk.Button(root,bg="#e9e9ed",fg="#333333",justify="center",
                          font=tkFont.Font(family='Times',size=10),
                          text="Export Folder:")
        Button_ExportFolder.grid(row=13, column=0, rowspan=1, columnspan=1, sticky="nsew")
        Button_ExportFolder["command"] = self.Button_ExportFolder_command

        # Folder Listbox
        self.Listbox_ExportFolder=tk.Label(root,bg="#e9e9ed",fg="#333333",
                         justify="left", font=('Times',10),
                         text="Export Folder Path")
        self.Listbox_ExportFolder.grid(row=13, column=1, rowspan=1, columnspan=3, sticky="nsew")

        # Menu bar at top of screen
        menubar = tk.Menu(root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open Config", command=self.open_config)
        filemenu.add_command(label="Save Config", command=self.save_config)
        root.config(menu=menubar)
        menubar.add_cascade(label="Config", menu=filemenu)

    ####################################
    ######  ADDITIONAL FUNCTIONS  ######
    ####################################

    def group_files(self, file_list):
        label_csvs = []
        natural_csvs = []
        correction_csvs = []
        excess_csvs = []
        for line in file_list:
            if self.label_wavenum in line:
                label_csvs.append(line)
            elif self.natural_wavenum in line:
                natural_csvs.append(line)
            elif self.correction_wavenum in line:
                correction_csvs.append(line)
            else:
                excess_csvs.append(line)
                    
        groups = []
        for i in range(len(label_csvs)):
            groups.append([label_csvs[i]])
            for line in natural_csvs:
                if line.replace(self.natural_wavenum,"") ==\
                      label_csvs[i].replace(self.label_wavenum,""):
                    groups[i].append(line)
                    break
            for line in correction_csvs:
                if line.replace(self.correction_wavenum,"") ==\
                      label_csvs[i].replace(self.label_wavenum,""):
                    groups[i].append(line)
                    break
        return groups
    
    def save_wavenum_image(self, filepath, title):
        plt.clf()
        plt.imshow(np.loadtxt(filepath, delimiter=','), cmap='CMRmap',vmin=0)
        plt.colorbar()
        plt.savefig(title + ".jpg", dpi = self.dpi)
        plt.clf()
        return
    
    def save_ratio_image(self, ratio, title):
        plt.imshow(ratio, cmap='CMRmap',vmin=0)
        plt.colorbar()
        plt.savefig(title + ".jpg", dpi = self.dpi)
        return

    def compute_ratio(self, label_fname, natural_fname,
                      correction_fname, title):
        # Load data
        correction_data = np.loadtxt(correction_fname, delimiter=',')
        label_data = np.loadtxt(label_fname, delimiter=',')
        natural_data = np.loadtxt(natural_fname, delimiter=',')

        # Correct data
        try:
            label_corrected = msa.correct_spectra(label_data,correction_data,
                                                    self.lcf)
            natural_corrected = msa.correct_spectra(natural_data,
                                                    correction_data,
                                                    self.natural_cf)
            natural_thresholded, maxsignal = msa.threshold(natural_corrected,
                                                            self.threshold)
            ratio = msa.compute_ratio(label_corrected, natural_thresholded)
        except:
            print('Error in ' + label_fname + " or other wavenumbers")

        ### Summarizing data
        summary = msa.summarize(ratio, header_name=title)
        summary = np.append(summary, [[maxsignal], ["Max Signal"]] , axis=1)

        return ratio, summary

    def sort_wavenumbers(self, group):
        correction_wavenum = self.correction_wavenum
        natural_wavenum = self.natural_wavenum
        label_wavenum = self.label_wavenum
        for file in group:
            if label_wavenum in file:
                label_file = file
            elif natural_wavenum in file:
                natural_file = file
            elif correction_wavenum in file:
                correction_file = file
            else:
                warnings.warn("Warning: " + file
                              + " could not be sorted into a wavenumber group")
        return label_file, natural_file, correction_file

    ####################################
    #########  GUI WIDGETS   ###########
    ####################################

    def update_listbox(self):
        self.ListBox_1.delete(0,tk.END)
        if self.show_fullpath:
            self.ListBox_1.insert(tk.END, *self.df['fpath'].values)
            return
        self.ListBox_1.insert(tk.END, *self.df['fname'].values)
        return

    def Button_Add_command(self):
        # Add files to the listbox
        ## Open file dialog
        files = tk.filedialog.askopenfilenames(
            filetypes=(("Comma Delimited", "*.csv"), ("All files", "*.*"),))
        
        outfolder = self.export_folder
        if self.subdivide_files:
            parent = Path(files[0]).parent.name
            outfolder = os.path.join(self.export_folder, parent)
        Path(outfolder).mkdir(parents=True, exist_ok=True)
        for file in files:
            # If the file is not already in the dataframe, add it
            if file not in self.df['fpath'].unique():
                outpath = os.path.join(outfolder, Path(file).stem)
                im_path = outpath + ".jpg"
                summary = msa.summarize(np.loadtxt(file, delimiter=','))
                print(summary)
                summary = list(summary[0].astype('float'))
                self.df.loc[self.df.shape[0]] = [file, Path(file).stem,
                                                 im_path,""] + summary
                self.save_wavenum_image(file, outpath)
                
        self.update_listbox()

    def Button_Delete_command(self):
        idx_to_del = list(self.ListBox_1.curselection())
        idx_to_del.sort()
        for i in range(len(idx_to_del)):
            self.ListBox_1.delete(idx_to_del[i]-i)
        self.df = self.df.drop(idx_to_del).reset_index(drop=True)
        print(self.df['fname'].values)

    def show_analyzed_files(self,files):
        self.ListBox_1.delete(0,tk.END)
        for file in files:
            self.ListBox_1.insert(tk.END, file)

    def Button_SaveList_command(self):
        print("command")
    
    def Button_Analyze_command(self):
        self.summary_df = pd.DataFrame(
            columns=['Filename','Mean', 'Median','Standard Deviation',
                     'Standard Error', 'Size', 'Max_Signal'])
        
        self.label_wavenum = self.lw_entry.get()
        self.natural_wavenum = self.nw_entry.get()
        self.correction_wavenum = self.lcw_entry.get()
        self.threshold = float(self.threshold_entry.get())
        self.lcf = float(self.lcf_entry.get())
        self.natural_cf = float(self.ncf_entry.get())

        groups = self.group_files(self.ListBox_1.get(0, tk.END))
        groups = np.array(groups)
        groups_flat = groups.flatten()

        # Create list of filenames for ratio images, including group number
        ratio_array = np.zeros(len(groups)).astype('str')
        for i in range(len(groups)):
            label_file, _, _ =self.sort_wavenumbers(groups[i])
            ratio_array[i] = (str(i) + "_" +Path(label_file)
                                  .stem.replace(self.label_wavenum, "")
                                  + "ratio")
        # groupstr = "Groups:\n"
        # for i in range(len(groups)): #TODO: Switch to confirm groups
        #     groupstr += str(i) + ": " + str(groups[i]) + "\n"
        # tk.messagebox.showinfo("Groups", groupstr)

        self.isAnalyzed = True
        self.show_analyzed_files(groups_flat)
        for i in range(len(groups)):
            # TODO: Confirm groups
            label_file, natural_file, correction_file =self.sort_wavenumbers(groups[i])
            self.save_wavenum_image(label_file,
                                    str(i) + "_" + Path(label_file).stem)
            self.save_wavenum_image(natural_file,
                                    str(i) + "_" + Path(natural_file).stem)
            self.save_wavenum_image(correction_file,
                                    str(i) + "_" + Path(correction_file).stem)
            ratio, summary = self.compute_ratio(label_file,natural_file, correction_file,
                str(i) + "_" + Path(label_file)
                .stem.replace(self.label_wavenum, ""))
            self.save_ratio_image(ratio,
                                  str(i) + "_" +Path(label_file)
                                  .stem.replace(self.label_wavenum, "")
                                  + "ratio")
            self.summary_df.loc[self.summary_df.shape[0]] = summary[0]
    def Button_NaturalImage_command(self):
        print("command")

    def Button_CorrectionImage_command(self):
        print("command")

    def Button_ExportFolder_command(self):
        self.export_folder = tk.filedialog.askdirectory()
        self.Listbox_ExportFolder['text'] = self.export_folder

    def Button_ExportStats_command(self):
        self.summary_df.to_csv("Summary.csv", mode='a')

    def display_images(self, index):
        # index = int(index//3)
        im_path = self.df['im_path'][index]
        img_width = self.img_panel.winfo_width()
        img_height = self.img_panel.winfo_height()

        self.panel_img = ImageTk.PhotoImage(Image.open(im_path)
                                            .resize((img_width,img_height)))
        self.img_panel.configure(image=self.panel_img)
        return
        
    def display_statistics(self, index):
        # fname = str(index) + "_" + Path(value).stem#.replace(self.label_wavenum, "").replace(self.natural_wavenum, "").replace(self.correction_wavenum, "")
        stats = np.round(self.df.loc[index][4:].astype(float),3)
        stats = ("Mean:"+ str(stats[0]) +", Median:"+str(stats[1])+
                 ", Max:"+str(stats[2])+", Stdev:"+str(stats[3])+
                 ", SE:"+str(stats[4])+",  Count: "+str(int(stats[5])))
        self.Button_Statistics.configure(text=stats)

    def On_File_Selection(self,evt):
        w = evt.widget
        index = int(w.curselection()[0])
        value = w.get(index)
        print('You selected item %d: "%s"' % (index, value))
        self.Button_Filename.configure(text=Path(value).stem)
        self.display_images(index)
        self.display_statistics(index)

    def open_config(self):
        return
    
    def save_config(self):
        return

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
