import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import warnings
from pathlib import Path
import multispectral_analysis as msa

class MultispectralModel:
    def __init__(self):
        # Initialize master DataFrame and other variables/booleans 
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
        lc_csvs = []
        nc_csvs = []
        excess_csvs = []
        # TODO: Have two separate correction wavenumbers
        # Categorize files into label, natural, correction, and excess groups
        for line in file_list:
            if label_wavenum in line:
                label_csvs.append(line)
            elif natural_wavenum in line:
                natural_csvs.append(line)
            elif label_correction_wavenum in line:
                lc_csvs.append(line)
            elif natural_correction_wavenum in line:
                nc_csvs.append(line)
            else:
                excess_csvs.append(line)

        groups = []
        # Create groups of related files (label, natural, correction)
        for i in range(len(label_csvs)):
            target = label_csvs[i].replace(label_wavenum, "")
            groups.append([label_csvs[i]])
            groups[i].append(self.match_csv(natural_csvs, natural_wavenum, target))
            groups[i].append(self.match_csv(lc_csvs, label_correction_wavenum, target))
            # TODO: Have two separate correction wavenumbers

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
        return
    
    def export_filelist(self):
        self.df['fpath'].to_csv(os.path.join(self.export_folder, f"fpaths_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"), index=False, mode = 'w')
        return
    
    def import_filelist(self):
        file_of_files = askopenfilenames(filetypes=(("Comma Delimited", "*.csv"), ("All files", "*.*"),))
        df = pd.read_csv(file_of_files[0])
        df = df[~df.applymap(lambda x: isinstance(x, str) and "ratio" in x.lower()).any(axis=1)]
        filelist = df['fpath'].tolist()
        print(filelist)
        self.add_files(filelist)
        return