import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import warnings
from pathlib import Path
import multispectral_analysis as msa
from mpl_toolkits.axes_grid1 import make_axes_locatable

class MultispectralModel:
    def __init__(self):
        # Initialize master DataFrame and other variables/booleans 
        self.df = pd.DataFrame(columns=['fpath', 'fname', 'im_path', 'hist_path', 'group', 'type',
                                        'Mean', 'Median', 'Max_Signal', 'Standard Deviation',
                                        'Standard Error', 'Count'])
        self.files = []  # List to hold file paths
        self.isAnalyzed = False  # Flag to check if files are analyzed
        self.dpi = 300  # DPI setting for image saving
        self.export_folder = "msa_analysis"  # Default export folder
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
        # Error case
        if label_corr is None:
            label_corr = ""
        if natural_corr is None:
            natural_corr = ""
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

    def assign_groups(self, groups_df: pd.DataFrame):
        for idx, row in groups_df.iterrows():
            # Slice columns from [1:] to remove identifier column
            for column in groups_df.columns[1:]:
                ## Place group number in row for each group in the class-wide dataframe
                self.df.loc[self.df['fpath'] == row[column], 'group'] = idx
        return

    # Function to save a data array as an image
    def save_image(self, data, title):
        # plt.clf()
        plt.grid(False)
        plt.imshow(data, cmap='CMRmap', vmin=0)
        plt.colorbar()
        plt.tight_layout(pad=2)
        self.saveimg(title)
        plt.close()
        return

    def save_data(self, data, title):
        np.savetxt(title + ".csv", data, delimiter=",")
        return

    # Function to compute ratio images from freq1, freq2, and correction files
    def _correct_and_ratio(self, data, entries):
        freq1_corrected = data['freq1']
        freq2_corrected = data['freq2']
        # If correction data is provided, correct the data
        if data['freq1c'] is not None:
            freq1_corrected = msa.correct_spectra(data['freq1'], data['freq1c'], entries['freq1cf'])
        if data['freq2c'] is not None:
            freq2_corrected = msa.correct_spectra(data['freq2'], data['freq2c'], entries['freq2cf'])
        freq2_thresholded, _ = msa.threshold(freq2_corrected, entries['threshold'])
        ratio = msa.compute_ratio(freq1_corrected, freq2_thresholded)
        return freq1_corrected, freq2_corrected, freq2_thresholded, ratio

    # Function to sort files in a group into label, natural, and correction
    def sort_wavenumbers(self, group, label_wavenum, natural_wavenum, 
                         label_correction_wavenum, natural_correction_wavenum):
        for file in group:
            if label_wavenum in file:
                label_file = file
                self.df.loc[self.df['fpath'] == file, 'type'] = 'Label'
            elif natural_wavenum in file:
                natural_file = file
                self.df.loc[self.df['fpath'] == file, 'type'] = 'Natural'
            elif label_correction_wavenum in file:
                label_correction_file = file
                self.df.loc[self.df['fpath'] == file, 'type'] = 'Label_Corr'
            elif natural_correction_wavenum in file:
                natural_correction_file = file
                self.df.loc[self.df['fpath'] == file, 'type'] = 'Natural_Corr'
            else:
                warnings.warn("Warning: " + file + " could not be sorted into a wavenumber group")
        if label_correction_wavenum is None:
            label_correction_file = None
        if natural_correction_wavenum is None:
            natural_correction_file = None
        if label_correction_wavenum == natural_correction_wavenum:
            natural_correction_file = label_correction_file
        return label_file, natural_file, label_correction_file, natural_correction_file

    def get_dir(self, file):
        outfolder = self.export_folder
        if self.subdivide_files:
            parent = Path(file).parent.name
            outfolder = os.path.join(self.export_folder, parent)
        Path(outfolder).mkdir(parents=True, exist_ok=True)
        return outfolder

    # Function to add files to the model and process them
    def add_files(self, file, outfolder):
        # Add each unique file to the DataFrame with a summary and create an image
        if file in self.df['fpath'].unique():
            return
        
        # data = np.loadtxt(file, delimiter=',')
        data = self.load_files(file)
        if data == []:
            return
        data = data[0]
        outpath = os.path.join(outfolder, Path(file).stem)
        image_path = outpath + self.get_ext()
        hist_path = outpath + "_hist" + self.get_ext()
        summary = msa.summarize(data)
        summary = list(summary[0].astype('float'))
        self.df.loc[self.df.shape[0]] = [file, Path(file).stem, image_path, hist_path, 0, None] + summary
        self.save_image(data, outpath)
        self.create_histogram(data, outpath)
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
            # If the file path is None (i.e. file is unused), append None to the list
            if filepath is None:
                loaded_data.append(None)
                continue
            try:
                # data = np.loadtxt(filepath, delimiter=',')
                data = pd.read_csv(filepath, header=None).values
                if data.dtype == 'O':
                    raise Exception(filepath + " contains non-numeric data")
                loaded_data.append(data)
            except Exception as e:
                print(f"Error loading file {filepath}: {e}")
        
        return loaded_data

    def pre_analyze_files(self, entries):
        groups_df = self.group_files(self.df['fpath'], entries['freq1'], entries['freq2'],
                entries['freq1c'], entries['freq2c'])
        self.assign_groups(groups_df)
        
        groups = self.df['group'].unique()
        self.group_images = [None for _ in range(len(groups))]
        self.group_histograms = [None for _ in range(len(groups))]
        return groups

    def _save_output_data(self, freq1_corrected, freq2_corrected, freq2_thresholded,
                          ratio, entries, fname, options):
        if options['should_save_corrections']:
            self.save_data(freq1_corrected, fname+"_"+entries['freq1']+"_corr")
            self.save_data(freq2_corrected, fname+"_"+entries['freq2']+"_corr")
        if options['should_save_threshold']:
            self.save_data(freq2_thresholded, fname+"_"+entries['freq2']+"_thresh")
        ratio_fname = fname + "_ratio"
        ratio_im_path = os.path.join(self.export_folder, ratio_fname)
        self.save_image(ratio, ratio_im_path)
        self.create_histogram(ratio, ratio_im_path)

    def create_paths(self, fname, extra):
        fname = fname + extra
        image_path = os.path.join(self.export_folder, fname + self.get_ext())
        histogram_path = os.path.join(self.export_folder, fname + "_hist" +self.get_ext())
        return fname, image_path, histogram_path
    

    def _summarize_and_save_to_df(self, data, fname, group_idx=None, type=None):
        type_to_fname = {"Ratio": "_ratio"}
        summary = msa.summarize(data)
        summary = list(summary[0].astype('float'))
        fname, image_path, histogram_path = self.create_paths(fname, type_to_fname[type])
        self.df.loc[self.df.shape[0]] = [fname, fname, image_path, histogram_path, group_idx, type] + summary
        return
    # Function to analyze files and compute ratio images
    # Labels wavenumbers as freq1, freq2, freq1c, and freq2c,
    # loads data, computes ratio, saves ratio, 
    def analyze_files(self, entries, group_idx):
        #TODO: Make sure refactor works. Implement options
        """
        Main function to analyze files. Groups files, asks if groups are correct, and computes ratio images. 
        """
        options = {"should_save_corrections": True, "should_save_threshold": True} # dummy variable for now
        data, fname = self._load_group(entries, group_idx)
        output_data = self._correct_and_ratio(data, entries)
        self._save_output_data(*output_data, entries, fname, options)
        ratio = output_data[3]
        self._summarize_and_save_to_df(ratio, fname, group_idx, 'Ratio')
        data['ratio'] = ratio
        if entries['freq1c'] == entries['freq2c']: # if correction file names are the same..
            data.pop('freq2c') # HACK: Should be named correction if the same 
            
        self.group_images[group_idx] = self.create_group_image(data, group_idx)
        self.group_histograms[group_idx] = self.create_group_histogram(data, group_idx)
        return
    
    def _load_group(self, entries, group_idx):
        fpaths = self._get_group(group_idx)
        fpaths = self.sort_wavenumbers(fpaths, entries['freq1'], entries['freq2'], entries['freq1c'], entries['freq2c'])
        fname = self._find_base_name(fpaths[0], entries['freq1'])
        data = self.load_files(*fpaths)
        data = {'freq1': data[0], 'freq2': data[1], 'freq1c': data[2], 'freq2c': data[3]}
        return data, fname

    def _get_group(self, idx):
        return self.df[self.df['group'] == idx]['fpath'].values

    def _find_base_name(self, file, extra):
        return Path(file).stem.replace(extra, "")
        
    def generate_group_figure(self, num_images):
        layout_mapping = {
            1: (1, 1),
            2: (1, 2),
            3: (1, 3),
            4: (2, 2),
            5: (2, 3)
        }

        # Create the figure and subplots
        plot_layout = layout_mapping[num_images]
        fig, axs = plt.subplots(plot_layout[0], plot_layout[1], figsize=(10, 5))
        plt.tight_layout(pad=2)
        axs = axs.flatten()
        return fig, axs
    
    def create_histogram(self, data, title):
        # fig, ax = self.generate_group_figure(1)
        fig, ax = plt.subplots(1, 1, figsize=(10, 5))
        plt.grid(False)
        msa.histogram(data, ax=ax, lower_bound=0)
        plt.tight_layout(pad=2)
        self.saveimg(title + "_hist")
        plt.close()
        return
        

    def create_group_histogram(self, data, group_id):
        df_slice = self.df[self.df['group'] == group_id]
        fig, axs = self.generate_group_figure(len(df_slice))
        # max_value = self.find_max_value(df_slice) # First 4 elements are non-ratio matrices

        for i, description in enumerate(data.keys()): # Note: Only works in Python 3.7+. Otherwise, data is not ordered.
            selected = data[description]
            ax = axs[i]
            msa.histogram(selected, ax=ax, lower_bound=0)
            # ax.histogram(selected, cmap='CMRmap', vmin=0, vmax=max_value) #####################
            ax.set_title(description)

        hist_path = os.path.join(self.export_folder, "group_histogram_" + str(group_id)) #TODO: Make exporting a different function
        self.saveimg(hist_path)
        plt.close()
        return hist_path + self.get_ext()

    def create_image(self, data, title, ax, max_value):
        im = ax.imshow(data, cmap='CMRmap', vmin=0, vmax=max_value)
        ax.set_title(title)
        ax.axis('off')

        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        plt.colorbar(im, cax=cax)
        plt.tight_layout(pad=2)

        return

    def create_group_image(self, data, group_id):
        df_slice = self.df[self.df['group'] == group_id]
        fig, axs = self.generate_group_figure(len(df_slice))
        max_value = self.find_max_value(df_slice) # First 4 elements are non-ratio matrices

        # If there is only 1 key in data.keys() with the substring "_Corr", then rename the key "Label_Corr" to "Correction"
        if len([key for key in data.keys() if "c" in key]) == 1:
            data["Correction"] = data.pop("freq1c")
        # If None is in the dictionary, remove the key
        keys_to_remove = [k for k, v in data.items() if v is None]
        for key in keys_to_remove:
            del data[key]
        
        ratio = data.pop("ratio")

        for i, description in enumerate(data.keys()):
            selected = data[description]    
            self.create_image(selected, description, axs[i], max_value)

        # Create the ratio image
        self.create_image(ratio, "ratio", axs[-1], ratio.max())

        img_path = os.path.join(self.export_folder, "group_" + str(group_id)) #TODO: Make exporting a different function
        self.saveimg(img_path)
        plt.close()
        return img_path + self.get_ext()

    def find_max_value(self, df: pd.DataFrame, include_ratio=False) -> float:
        """ Helper function to find the maximum value among matrices in a DataFrame.
        Optionally include ratio images. """
        idx = df['type'] != 'ratio'
        if include_ratio:
            idx = slice(None)
        return df.loc[idx, 'Max_Signal'].max()

    def get_df_slice(self, index):
        """ Helper function to get a slice of the DataFrame
        based on the given index and filter options. """
        return self.df.loc[index, :]
    
    def get_single_histogram(self, df_slice):
        return df_slice.loc['hist_path']

    def get_group_histogram(self, group_id):
        return self.group_histograms[group_id]

    def get_single_image(self, df_slice):
        return df_slice.loc['im_path']

    def get_group_image(self, group_id):
        return self.group_images[group_id]

    def get_ext(self):
        return self.export_filetype
    
    def set_ext(self, filetype):
        self.export_filetype = filetype
        return

    def saveimg(self, title):
        plt.savefig(title + self.get_ext(), dpi=self.dpi)
        return
        # if not self.export_fig:
        #     return
        # # plt.savefig(title + ".fig", dpi='figure')
        # savemat(title + ".mat", {'data': plt.gcf()})
        
    # Function to export the statistics to a CSV file
    def export_stats(self):
        self.df.to_csv(os.path.join(self.export_folder, "Summary.csv"), mode='a')
        return
    
    def export_filelist(self):
        # Ask for file name and location
        
        self.df['fpath'].to_csv(os.path.join(self.export_folder, f"fpaths_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"), index=False, mode = 'w')
        return