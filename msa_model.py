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
        self.df = pd.DataFrame(columns=['fpath', 'fname', 'im_path', 'hist_path', 'group', 'isRatio',
                                        'Mean', 'Median', 'Max_Signal', 'Standard Deviation',
                                        'Standard Error', 'Count'])
        self.files = []  # List to hold file paths
        self.isAnalyzed = False  # Flag to check if files are analyzed
        self.dpi = 300  # DPI setting for image saving
        self.export_folder = "msa_analysis"  # Default export folder
        self.show_fullpath = False  # Flag to show full file paths
        self.show_parent = False  # Flag to show parent folder
        self.subdivide_files = True  # Flag to subdivide files into folders

    def group_files(self, file_list: list, label: str, natural: str, label_corr:str, natural_corr: str) -> pd.DataFrame:
        """
        Groups files based on shared common name
        Parameters
        -----------
        file_list : list
            List of file names.
        label: str
            Wavenumber used as the label.
        natural: str
            Wavenumber used as the control/natural.
        label_corr: str
            Wavenumber used to correct label wavenumber intensity.
        natural_corr: str
            Wavenumber used to correct label wavenumber intensity.

        Returns
        -------
        df : pandas.DataFrame
            DataFrame containing the grouped files.
        """
        df = pd.DataFrame(columns=["identifier", "label", "natural", "label_corr", "natural_corr"], dtype=str)
        for file in file_list:
            identifier = (file
                          .replace(label, "")
                          .replace(natural, "")
                          .replace(label_corr, "")
                          .replace(natural_corr, ""))
            if identifier not in df["identifier"].values:
                df.loc[df.shape[0]] = [identifier, "", "", "", "",]
            idx = df[df["identifier"] == identifier].index[0]
            if label in file:
                df.loc[idx, "label"] = file
            elif natural in file:
                df.loc[idx, "natural"] = file
            elif label_corr in file:
                df.loc[idx, "label_corr"] = file
            elif natural_corr in file:
                df.loc[idx, "natural_corr"] = file

        return df

    def request_group_check(self, groups_df: pd.DataFrame):
        #TODO: Implement a GUI to ask user if groups are correct 
        return groups_df

    def assign_groups(self, groups_df: pd.DataFrame):
        for idx, row in groups_df.iterrows():
            # Slice columns from [1:] to remove identifier column
            for column in groups_df.columns[1:]:
                ## Place group number in row for each group in the class-wide dataframe
                self.df.loc[self.df['fpath'] == row[column], 'group'] = idx
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
                self.df.loc[self.df.shape[0]] = [file, Path(file).stem, image_path, "", 0, False] + summary
                self.save_wavenum_image(file, outpath)

        return
    
    def load_files(self, *filepaths):
        """
        Loads multiple files using np.loadtxt and returns the loaded data.
        
        Parameters
        ----------
        *filepaths : str
            Any number of file paths to load.

        Returns
        --------
        out : list
        A list of numpy arrays containing the data from the files.
        """
        loaded_data = []
        
        for filepath in filepaths:
            try:
                data = np.loadtxt(filepath, delimiter=',')
                loaded_data.append(data)
            except Exception as e:
                print(f"Error loading file {filepath}: {e}")
        
        return loaded_data

    # Function to analyze files and compute ratio images
    def analyze_files(self, label_wavenum, natural_wavenum, label_correction_wavenum, natural_correction_wavenum, threshold, lcf, natural_cf):        
        """
        Main function to analyze files. Groups files, asks if groups are correct, and computes ratio images. 
        """


        groups_df = self.group_files(self.df['fpath'], label_wavenum, natural_wavenum,
                        label_correction_wavenum, natural_correction_wavenum)
        groups_df = self.request_group_check(groups_df)
        self.assign_groups(groups_df)
        
        groups = self.df['group'].unique()
        for group_idx in groups:
            group = self.df[self.df['group'] == group_idx]['fpath'].values
            label_file, natural_file, label_correction_file, natural_correction_file = self.sort_wavenumbers(group, label_wavenum, natural_wavenum,
                                                                              label_correction_wavenum, natural_correction_wavenum)
            label_data, natural_data, label_correction_data, natural_correction_data = self.load_files(
                label_file, natural_file, label_correction_file, natural_correction_file
                )
            ratio = self.ratio_images(label_data, natural_data, label_correction_data, natural_correction_data,
                                      lcf, natural_cf, threshold)
            ratio_fname = Path(label_file).stem.replace(label_wavenum, "") + "_ratio"
            ratio_im_path = os.path.join(self.export_folder, ratio_fname)
            self.save_image(ratio, ratio_im_path)
            summary = msa.summarize(ratio)
            summary = list(summary[0].astype('float'))
            self.df.loc[self.df.shape[0]] = [ratio_fname, ratio_fname, ratio_im_path + ".jpg", "", group_idx, True] + summary
    # Function to export the statistics to a CSV file
    def export_stats(self):
        self.df.to_csv(os.path.join(self.export_folder, "Summary.csv"), mode='a')
        return
    
    def export_filelist(self):
        self.df['fpath'].to_csv(os.path.join(self.export_folder, f"fpaths_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"), index=False, mode = 'w')
        return
    
    def import_filelist(self, file_df):
        # file_of_files = askopenfilenames(filetypes=(("Comma Delimited", "*.csv"), ("All files", "*.*"),))
        # df = pd.read_csv(file_of_files[0])
        file_df = file_df[~file_df.applymap(lambda x: isinstance(x, str) and "ratio" in x.lower()).any(axis=1)]
        filelist = file_df['fpath'].tolist()
        print(filelist)
        self.add_files(filelist)
        return